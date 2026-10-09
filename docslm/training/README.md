# DocSLM training on an RTX 4090 (24 GB)

Full fine-tune of Qwen3.5-0.8B fits comfortably on a 4090 with the memory
recipe below. Two stages: SFT on the 930 reasoned trajectories, then DPO on
the 240 reasoning-contrastive preference pairs.

## 1. Environment

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install transformers trl peft datasets accelerate bitsandbytes sentencepiece
pip install flash-attn --no-build-isolation        # optional, ~2x speed; skip if the build fails
huggingface-cli login                              # needed once for Qwen weights
```

## 2. SFT (stage 1) — ~15–30 min

```bash
# a) render + mask once (CPU): loss only on assistant <think>+tool-call tokens.
#    Verified on this dataset: 920/930 kept (10 skipped >6144 tok),
#    1.8M tokens/epoch, ~50% of tokens are assistant tokens (reasoning+code).
python3 training/prep_sft_data.py --data datasets/sft_trajectories.jsonl \
    --out datasets/sft_tokenized.jsonl --max-len 6144

# b) full fine-tune
python3 training/train_sft.py --data datasets/sft_tokenized.jsonl --out runs/sft-v1
```

Memory recipe (what makes full-FT fit in 24 GB): bf16 weights, `paged_adamw_8bit`,
gradient checkpointing, batch 2 × accum 16 @ ≤6144 tokens, frozen vision tower
(text-only training). Peak ≈ 14–18 GB.

Defaults: LR 1e-5 cosine, 3 epochs, warmup 3%, clip 1.0 (per
[04_TRAINING_PIPELINE.md](../docs/04_TRAINING_PIPELINE.md) §2). If you OOM:
`--batch 1` first, then `--lora` (r=64 α=128, ~12 GB, merges on save).

## 3. DPO (stage 2) — ~15–30 min

```bash
python3 training/train_dpo.py --sft runs/sft-v1/final --out runs/dpo-v1
```

Chosen = full plan reasoning + verified code; rejected = shallow reasoning +
measured-failing code (β 0.1, LR 5e-7, 1 epoch). Tool calls are flattened to
`<tool_call>` text for the DPO loss.

## 4. Sanity-check the result

```bash
python3 - <<'EOF'
from transformers import AutoTokenizer, AutoModelForCausalLM
import json
tok = AutoTokenizer.from_pretrained("runs/dpo-v1/final")
model = AutoModelForCausalLM.from_pretrained("runs/dpo-v1/final", device_map="cuda")
rec = json.loads(open("datasets/sft_trajectories.jsonl").readline())
prompt = tok.apply_chat_template(rec["messages"][:2], tools=rec["tools"],
                                 add_generation_prompt=True, tokenize=False)
ids = tok(prompt, return_tensors="pt").to("cuda")
out = model.generate(**ids, max_new_tokens=600, do_sample=False)
print(tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=False))
EOF
```

Expect: a `<think>` route/plan block, then a single well-formed tool call.

## 5. Ship to llama.cpp (the PRD's deployment target)

```bash
git clone --depth 1 https://github.com/ggml-org/llama.cpp
python3 llama.cpp/convert_hf_to_gguf.py runs/dpo-v1/final --outfile docslm-f16.gguf
./llama.cpp/llama-quantize docslm-f16.gguf docslm-q4_k_m.gguf Q4_K_M
# gate check: re-run data_engine.validate-style spot checks against the Q4 model
```

Ship gate (per [05_EVALUATION.md](../docs/05_EVALUATION.md) §4): Q4_K_M must hold
gate B within −2 pts; if it doesn't, default to Q5_K_M and file a QAT task.

## Notes

- `prep_sft_data.py` serializes to Qwen3's native chat format directly
  (`im_start` blocks, `<tool_response>` for results, `<tool_call>` JSON for
  actions) and masks everything except assistant spans (reasoning + tool calls
  + final summary). The dry-run verifier in this repo confirmed: system/user/
  tool results masked, all `<think>` blocks and `<tool_call>` blocks trained,
  ~50% assistant-token ratio.
- Skipped-overlong records (rare; expect <5%) are counted in the prep output —
  raise `--max-len 8192` (batch 1) if you want zero drops.
- Keep seed 2026 end-to-end for run comparability; every released checkpoint
  should record: data manifest hash + this scripts' commit + GGUF digest.
