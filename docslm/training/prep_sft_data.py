"""Render DocSLM trajectories with the Qwen3 chat format and build
assistant-only loss masks.

Serialization follows Qwen3's documented native format (no dependency on the
HF chat template, whose generation-prompt/think-header behavior differs from
our per-turn ground truth):

  <|im_start|>system\n{content}<|im_end|>\n
  <|im_start|>user\n{content}<|im_end|>\n
  <|im_start|>user\n<tool_response>\n{content}<|im_end|>\n
  <|im_start|>assistant\n<think>…</think>\n<tool_call>\n{"name":…,"arguments":{…}}\n</tool_call><|im_end|>\n

Labels train ONLY on assistant spans (think + tool calls + final summary);
system/user/tool text is masked to -100.

Usage:
  python3 training/prep_sft_data.py --data datasets/sft_trajectories.jsonl \
      --out datasets/sft_tokenized.jsonl --max-len 6144
"""
import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer

MODEL = "Qwen/Qwen3.5-0.8B"


def _tool_call_text(call: dict) -> str:
    fn = call["function"]
    args = fn["arguments"]
    if isinstance(args, str):
        args = json.loads(args)
    return ('<tool_call>\n{"name": "' + fn["name"] + '", "arguments": '
            + json.dumps(args, ensure_ascii=False) + "\n}\n</tool_call>")


def render_text(messages) -> str:
    """Serialize the full conversation to Qwen3 chat text."""
    out = []
    for m in messages:
        role = m["role"]
        if role == "system":
            out.append(f"<|im_start|>system\n{m['content']}<|im_end|>\n")
        elif role == "user":
            out.append(f"<|im_start|>user\n{m['content']}<|im_end|>\n")
        elif role == "tool":
            out.append(f"<|im_start|>user\n<tool_response>\n{m['content']}"
                       f"<|im_end|>\n")
        elif role == "assistant":
            body = m.get("content") or ""
            calls = m.get("tool_calls") or []
            if calls:
                body = body + "\n" + "\n".join(_tool_call_text(c) for c in calls)
            out.append(f"<|im_start|>assistant\n{body}<|im_end|>\n")
    return "".join(out)


def render_example(tok, messages) -> tuple:
    """Tokenize per turn: assistant spans trained, everything else masked.

    Assistant turn text is constructed from its own content (+tool calls), so
    the trained span is exactly what the model must emit at inference."""
    input_ids, labels = [], []
    for m in messages:
        if m["role"] == "assistant":
            body = m.get("content") or ""
            calls = m.get("tool_calls") or []
            if calls:
                body = body + "\n" + "\n".join(_tool_call_text(c) for c in calls)
            turn = f"<|im_start|>assistant\n{body}<|im_end|>\n"
            ctx = f"<|im_start|>assistant\n"
            ctx_ids = tok(ctx, add_special_tokens=False)["input_ids"]
            turn_ids = tok(turn, add_special_tokens=False)["input_ids"]
            input_ids.extend(ctx_ids)
            labels.extend([-100] * len(ctx_ids))
            input_ids.extend(turn_ids[len(ctx_ids):])
            labels.extend(turn_ids[len(ctx_ids):])
        else:
            text = render_text([m])
            ids = tok(text, add_special_tokens=False)["input_ids"]
            input_ids.extend(ids)
            labels.extend([-100] * len(ids))
    return input_ids, labels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="datasets/sft_trajectories.jsonl")
    ap.add_argument("--out", default="datasets/sft_tokenized.jsonl")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--max-len", type=int, default=6144)
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.model)
    kept, skipped, lens = 0, 0, []
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for line in Path(args.data).open():
            rec = json.loads(line)
            ids, labels = render_example(tok, rec["messages"])
            if len(ids) > args.max_len:
                skipped += 1
                continue
            lens.append(len(ids))
            kept += 1
            f.write(json.dumps({"id": rec["id"], "input_ids": ids,
                                "labels": labels}) + "\n")

    lens.sort()
    n = len(lens)
    print(f"kept {kept}, skipped (>{args.max_len} tok): {skipped}")
    if n:
        print(f"token lens: min={lens[0]} p50={lens[n // 2]} "
              f"p90={lens[int(n * 0.9)]} max={lens[-1]} "
              f"total={sum(lens):,} ({sum(lens) / 1e6:.1f}M tokens/epoch)")
    sample = [json.loads(l) for _, l in zip(range(200), out.open())]
    tot = sum(len(s["input_ids"]) for s in sample)
    trn = sum(sum(1 for t in s["labels"] if t != -100) for s in sample)
    print(f"assistant-token ratio (200-sample): {trn / max(tot, 1):.1%}")


if __name__ == "__main__":
    main()
