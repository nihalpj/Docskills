#!/usr/bin/env bash
# =============================================================================
# DocSLM one-shot training driver
#
# Automates the Stage-B SFT workflow from docs/08_NOVITA_4090_TRAINING.md:
#   preflight -> deps -> flash-attn -> base model -> tokenize -> train -> rescue
#
# Usage (on the Novita 4090 instance, inside tmux):
#   bash training/train.sh
#   HF_TOKEN=hf_xxx UPLOAD_REPO=<you>/docslm-sft-v1 bash training/train.sh
#
# Knobs (environment variables):
#   OUT=runs/sft-v1        output dir (checkpoints + final/)
#   MODEL=Qwen/Qwen3.5-0.8B
#   EPOCHS=3  LR=1e-5      training hyperparameters
#   BATCH=2  ACCUM=16      per-device batch x grad accumulation (effective 32)
#   MAX_LEN=6144           tokenization cutoff
#   LORA=1                 LoRA fallback instead of full fine-tune
#   RESUME=1               resume from the latest checkpoint-* in OUT
#   FLASH_ATTN=auto|skip   skip -> SDPA attention (~2x slower, no build step)
#   SKIP_DEPS=1            don't touch pip
#   REBUILD_DATA=1         rerun data_engine.build + validate first
#   FORCE_PREP=1           rerun tokenization even if output is newer than input
#   UPLOAD_REPO=<repo/id>  push OUT/final to Hugging Face when done
#   GPU_PRICE=0.35         $/GPU-hour used for the cost line
# =============================================================================
set -euo pipefail

# always run with bash, from the repo root (one level above this script)
if [ -z "${BASH_VERSION:-}" ]; then exec bash "$0" "$@"; fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ---------- configuration (env overridable) --------------------------------
DATA_RAW="${DATA_RAW:-datasets/sft_trajectories.jsonl}"
DATA_TOK="${DATA_TOK:-datasets/sft_tokenized.jsonl}"
OUT="${OUT:-runs/sft-v1}"
MODEL="${MODEL:-Qwen/Qwen3.5-0.8B}"
EPOCHS="${EPOCHS:-3.0}"
LR="${LR:-1e-5}"
BATCH="${BATCH:-2}"
ACCUM="${ACCUM:-16}"
MAX_LEN="${MAX_LEN:-6144}"
UPLOAD_REPO="${UPLOAD_REPO:-}"
FLASH_ATTN="${FLASH_ATTN:-auto}"          # auto | skip
SKIP_DEPS="${SKIP_DEPS:-0}"
REBUILD_DATA="${REBUILD_DATA:-0}"
FORCE_PREP="${FORCE_PREP:-0}"
GPU_PRICE="${GPU_PRICE:-0.35}"
export HF_HUB_ENABLE_HF_TRANSFER="${HF_HUB_ENABLE_HF_TRANSFER:-1}"

# ---------- logging ----------------------------------------------------------
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  B=$'\e[1m' G=$'\e[32m' Y=$'\e[33m' R=$'\e[31m' N=$'\e[0m'
else B='' G='' Y='' R='' N=''; fi
info() { printf '%s\n' "${G}▸${N} $*"; }
warn() { printf '%s\n' "${Y}▲${N} $*"; }
err()  { printf '%s\n' "${R}✖ $*${N}" >&2; }
die()  { err "$*"; exit 1; }
step() { printf '\n%s━━ %s ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%s\n' "$B" "$*" "$N"; }

START=$SECONDS
fmt_time() { printf '%dm%02ds' $(( ($1) / 60 )) $(( ($1) % 60 )); }

# hf CLI moved between releases (huggingface-cli -> hf); support both
HF_BIN=''
hfcli() {
  if [ -z "$HF_BIN" ]; then
    if command -v hf >/dev/null 2>&1; then HF_BIN=hf; else HF_BIN=huggingface-cli; fi
  fi
  "$HF_BIN" "$@"
}

# ---------- preflight --------------------------------------------------------
step "Preflight"
command -v python3 >/dev/null 2>&1 || die "python3 not found"
command -v nvidia-smi >/dev/null 2>&1 || die "nvidia-smi not found — no NVIDIA driver on this box"

python3 - <<'PY' || die "No usable CUDA GPU visible to torch (need a CUDA-enabled torch build + GPU)"
import torch
assert torch.cuda.is_available(), "torch.cuda.is_available() is False"
p = torch.cuda.get_device_properties(0)
print(f"GPU: {p.name} · {p.total_memory / 2**30:.0f} GiB · torch {torch.__version__}")
PY

if [ ! -f "$DATA_RAW" ]; then
  die "Training data missing: $DATA_RAW — run: python3 -m data_engine.build --n-sft 930 --n-routing 1240 --n-pref 240 --seed 2026"
fi

if [ -z "${TMUX:-}" ] && [ -z "${STY:-}" ]; then
  warn "Not inside tmux/screen — a dropped SSH connection kills the run. Recommended: tmux new -s docslm"
fi

free_kb="$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')"
if [ "$free_kb" -lt $((15 * 1024 * 1024)) ]; then
  warn "Less than 15 GB free under $ROOT — base model cache + checkpoints may not fit"
fi

if [ -d "$OUT/final" ]; then
  warn "$OUT/final already exists and will be overwritten — use OUT=$OUT-v2 to keep it"
fi

# ---------- dependencies -----------------------------------------------------
if [ "$SKIP_DEPS" != "1" ]; then
  step "Dependencies"
  if python3 - <<'PY' 2>/dev/null
import transformers
v = tuple(int(x) for x in transformers.__version__.split(".")[:2])
assert v >= (4, 51), transformers.__version__
import datasets, accelerate, peft, bitsandbytes, huggingface_hub
PY
  then
    info "Python deps present ($(python3 -c 'import transformers; print(transformers.__version__)'))"
  else
    info "Installing python deps…"
    pip install -q -U "transformers>=4.56,<5" datasets accelerate peft bitsandbytes huggingface_hub
  fi

  # flash-attention: train_sft.py uses it whenever CUDA is on; fall back to SDPA if missing
  if python3 -c "import flash_attn" 2>/dev/null; then
    info "flash-attn present"
  elif [ "$FLASH_ATTN" = "skip" ]; then
    warn "FLASH_ATTN=skip -> SDPA attention (~2x slower, identical results)"
    export ATTN_IMPL=sdpa
  else
    info "Installing flash-attn (prebuilt wheel; up to 20 min if it compiles)…"
    if timeout 1200 pip install -q flash-attn --no-build-isolation \
       && python3 -c "import flash_attn" 2>/dev/null; then
      info "flash-attn installed"
    else
      warn "flash-attn unavailable -> falling back to SDPA (~2x slower)."
      warn "For speed later, grab a matching wheel: https://github.com/Dao-AILab/flash-attention/releases"
      export ATTN_IMPL=sdpa
    fi
  fi
else
  info "SKIP_DEPS=1 — leaving the environment alone"
fi

# ---------- base model --------------------------------------------------------
step "Base model"
if [ -n "${UPLOAD_REPO:-}" ] && [ -z "${HF_TOKEN:-}" ] && ! hfcli auth whoami >/dev/null 2>&1; then
  die "UPLOAD_REPO is set but no Hugging Face auth found. Set HF_TOKEN (Novita: inject it as an instance env var) or run: hfcli auth login"
fi
info "Downloading $MODEL (skipped automatically if already cached)…"
hfcli download "$MODEL"

# ---------- data prep ---------------------------------------------------------
step "Tokenize"
if [ "$REBUILD_DATA" = "1" ]; then
  info "Rebuilding dataset from the data engine…"
  python3 -m data_engine.build --n-sft 930 --n-routing 1240 --n-pref 240 --seed 2026
  python3 -m data_engine.validate
fi
if [ "$FORCE_PREP" != "1" ] && [ "$DATA_TOK" -nt "$DATA_RAW" ]; then
  info "$DATA_TOK is up to date — skipping (FORCE_PREP=1 to rerun)"
else
  python3 training/prep_sft_data.py --data "$DATA_RAW" --out "$DATA_TOK" --max-len "$MAX_LEN"
fi

# ---------- training ----------------------------------------------------------
step "Train"
mode="full-FT"; if [ -n "${LORA:-}" ]; then mode="LoRA"; fi
info "out=$OUT · mode=$mode · epochs=$EPOCHS · lr=$LR · batch=$BATCH x $ACCUM · attn=${ATTN_IMPL:-flash_attention_2}"

ARGS=( --data "$DATA_TOK" --out "$OUT" --model "$MODEL"
       --epochs "$EPOCHS" --lr "$LR" --batch "$BATCH" --accum "$ACCUM" )
if [ -n "${LORA:-}" ]; then ARGS+=( --lora ); fi
if [ "${RESUME:-0}" = "1" ];   then ARGS+=( --resume ); fi

python3 training/train_sft.py "${ARGS[@]}"

# ---------- result ------------------------------------------------------------
step "Result"
[ -f "$OUT/final/config.json" ] || die "Training ended but $OUT/final is missing — scroll up for the error"
du -sh "$OUT/final"

elapsed=$(( SECONDS - START ))
printf '%s\n' "${G}▸${N} wall time: $(fmt_time "$elapsed") · compute ≈ \$$(python3 -c "print(round($GPU_PRICE * $elapsed / 3600, 2))") at \$${GPU_PRICE}/GPU-hr"

if [ -n "$UPLOAD_REPO" ]; then
  info "Uploading $OUT/final -> huggingface.co/$UPLOAD_REPO …"
  hfcli upload "$UPLOAD_REPO" "$OUT/final" --repo-type model
  info "Checkpoint is safe off this machine — you can stop the Novita instance now."
else
  warn "Checkpoint lives on this instance's EPHEMERAL disk — rescue it before stopping:"
  printf '   hfcli upload <you>/docslm-sft-v1 %s/final --repo-type model\n' "$OUT"
  printf '   or: scp -r -P <port> root@<host>:%s/%s/final .\n' "$ROOT" "$OUT"
fi

printf '%s\n' "${G}▸${N} Next: smoke-eval $OUT/final — 3–5 create-route prompts must emit valid <tool_call> JSON,"
printf '%s\n' "  then DPO on datasets/preference_pairs.jsonl (see docs/04_TRAINING_PIPELINE.md §3)."
info "Done in $(fmt_time "$elapsed")"
