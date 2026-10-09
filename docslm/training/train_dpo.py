"""Stage 2 — DPO on reasoning-contrastive preference pairs (RTX 4090).

Chosen = full plan reasoning + verified code; rejected = shallow reasoning +
code with a measured failure. DPO on these pairs teaches the model BOTH the
correct action and that skipping reasoning/verification is worse.

The assistant turns contain tool_calls, which we flatten into text
(<think> + <tool_call> JSON) so the plain-language-model DPO loss applies.

Usage:
  python3 training/train_dpo.py --sft runs/sft-v1/final --out runs/dpo-v1
"""
import argparse
import json

import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOConfig, DPOTrainer

MODEL = "Qwen/Qwen3.5-0.8B"


def flattenassistant(msg: dict) -> dict:
    """Serialize an assistant turn (think + tool_calls) to plain content text."""
    content = msg.get("content") or ""
    calls = msg.get("tool_calls") or []
    if calls:
        rendered = "\n".join(
            f'<tool_call>\n{{"name": "{c["function"]["name"]}", '
            f'"arguments": {c["function"]["arguments"]}}}\n</tool_call>'
            for c in calls)
        content = (content or "") + "\n" + rendered
    return {"role": "assistant", "content": content}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="datasets/preference_pairs.jsonl")
    ap.add_argument("--sft", default="runs/sft-v1/final",
                    help="SFT checkpoint to start from (DPO anchors to it)")
    ap.add_argument("--out", default="runs/dpo-v1")
    ap.add_argument("--beta", type=float, default=0.1)
    ap.add_argument("--lr", type=float, default=5e-7)
    ap.add_argument("--epochs", type=float, default=1.0)
    args = ap.parse_args()

    rows = []
    for line in open(args.data, encoding="utf-8"):
        rec = json.loads(line)
        rows.append({
            "prompt": rec["prompt"],                     # [system, user]
            "chosen": [flattenassistant(rec["chosen"])],
            "rejected": [flattenassistant(rec["rejected"])],
        })
    ds = Dataset.from_list(rows)

    tok = AutoTokenizer.from_pretrained(args.sft)
    model = AutoModelForCausalLM.from_pretrained(
        args.sft, dtype=torch.bfloat16, attn_implementation="flash_attention_2"
        if torch.cuda.is_available() else "sdpa")
    model.config.use_cache = False
    for n, p in model.named_parameters():
        if "visual" in n or "vision" in n:
            p.requires_grad = False

    conf = DPOConfig(
        output_dir=args.out,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        beta=args.beta,
        max_prompt_length=4096,
        max_length=6144,
        bf16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit",
        logging_steps=10,
        save_strategy="no",
        report_to=[],
        seed=2026,
    )
    trainer = DPOTrainer(model=model, args=conf, train_dataset=ds,
                         processing_class=tok)
    trainer.train()
    model.config.use_cache = True
    trainer.save_model(args.out + "/final")
    tok.save_pretrained(args.out + "/final")
    print(f"saved {args.out}/final")


if __name__ == "__main__":
    main()
