"""DocSLM SFT on a single RTX 4090 (24 GB) — full fine-tune of Qwen3.5-0.8B.

Memory recipe that makes full-FT fit in 24 GB:
  bf16 weights + paged_adamw_8bit (bitsandbytes) + gradient checkpointing +
  per-device batch 2 @ 6144 tokens + frozen vision tower (text-only training).

  ~1.6 GB weights + ~1.6 GB grads + ~3.2 GB 8-bit optimizer + activations
  -> ~14-18 GB peak; comfortable on 24 GB.

Expected wall clock (930 trajectories, ~2.5M train tokens/epoch, 3 epochs):
  ~30-60 min on a 4090 with flash-attn; ~2x that with sdpa.

Usage:
  python3 training/train_sft.py --data datasets/sft_tokenized.jsonl \
      --out runs/sft-v1
"""
import argparse
import json

import torch
from datasets import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer,
                          TrainingArguments)

MODEL = "Qwen/Qwen3.5-0.8B"


class Collator:
    """Pad input_ids/labels to the longest sequence in the batch."""

    def __init__(self, pad_id: int):
        self.pad_id = pad_id

    def __call__(self, feats):
        n = max(len(f["input_ids"]) for f in feats)
        input_ids, labels, attn = [], [], []
        for f in feats:
            pad = n - len(f["input_ids"])
            input_ids.append(f["input_ids"] + [self.pad_id] * pad)
            labels.append(f["labels"] + [-100] * pad)
            attn.append([1] * len(f["input_ids"]) + [0] * pad)
        return {"input_ids": torch.tensor(input_ids),
                "labels": torch.tensor(labels),
                "attention_mask": torch.tensor(attn)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="datasets/sft_tokenized.jsonl")
    ap.add_argument("--out", default="runs/sft-v1")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--accum", type=int, default=16)
    ap.add_argument("--lora", action="store_true",
                    help="LoRA fallback (~12 GB): r=64 alpha=128 on all linear layers")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.data, encoding="utf-8")]
    ds = Dataset.from_list(rows)
    tok = AutoTokenizer.from_pretrained(args.model)

    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.bfloat16, attn_implementation="flash_attention_2"
        if torch.cuda.is_available() else "sdpa")
    model.config.use_cache = False

    # text-only training: freeze the vision tower so it holds no optimizer state
    frozen = 0
    for n, p in model.named_parameters():
        if "visual" in n or "vision" in n:
            p.requires_grad = False
            frozen += p.numel()
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"trainable params: {trainable / 1e6:.0f}M "
          f"(frozen non-trainable: {frozen / 1e6:.0f}M)")

    if args.lora:
        from peft import LoraConfig, get_peft_model
        model = get_peft_model(model, LoraConfig(
            r=64, lora_alpha=128, lora_dropout=0.05, task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                            "gate_proj", "up_proj", "down_proj"]))
        model.print_trainable_parameters()

    targs = TrainingArguments(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=args.accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        weight_decay=0.0,
        max_grad_norm=1.0,
        bf16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit",
        logging_steps=10,
        save_strategy="steps",
        save_steps=200,
        save_total_limit=2,
        group_by_length=True,
        dataloader_num_workers=2,
        report_to=[],
        seed=2026,
    )

    Trainer(model=model, args=targs, train_dataset=ds,
            data_collator=Collator(tok.pad_token_id or tok.eos_token_id)).train()

    model.config.use_cache = True
    trainer_model = model
    if args.lora:
        trainer_model = model.merge_and_unload()
    trainer_model.save_pretrained(args.out + "/final")
    tok.save_pretrained(args.out + "/final")
    print(f"saved {args.out}/final")


if __name__ == "__main__":
    main()
