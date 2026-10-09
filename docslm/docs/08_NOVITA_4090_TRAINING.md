# Training DocSLM on Novita.ai — RTX 4090 Runbook

End-to-end guide for renting an **NVIDIA RTX 4090 (24 GB)** on [Novita AI GPU Cloud](https://novita.ai/gpus) and training **DocSLM-0.8B** (SFT stage of [04 — Training Pipeline](04_TRAINING_PIPELINE.md)) on it. Everything here was written against this repo's actual scripts (`training/prep_sft_data.py`, `training/train_sft.py`) and Novita's GPU Instance product as documented in their official guides.

> **TL;DR** — the whole SFT run (930 trajectories, 3 epochs, ~2.5M tokens/epoch) takes **~30–60 minutes of GPU time** and costs **under $1** of compute. Rent the 4090 on-demand, run one prep command and one training command, copy `runs/sft-v1/final` off the box (or push to Hugging Face), stop the instance. Details below.
>
> **Shortcut:** steps 5–10 below are automated by **`bash training/train.sh`** (run it inside tmux after connecting). It installs deps, fetches the model, tokenizes, trains, prints the cost line, and — if you set `UPLOAD_REPO=<you>/docslm-sft-v1` — uploads the checkpoint for you. The manual steps remain the reference for what it does.

---

## Table of contents

1. [Why a single 4090 is enough](#1-why-a-single-4090-is-enough)
2. [Prerequisites](#2-prerequisites)
3. [Step 1 — Launch the instance](#3-step-1--launch-the-instance)
4. [Step 2 — Connect (SSH / JupyterLab)](#4-step-2--connect-ssh--jupyterlab)
5. [Step 3 — Verify the environment](#5-step-3--verify-the-environment)
6. [Step 4 — Upload the repo and data](#6-step-4--upload-the-repo-and-data)
7. [Step 5 — Install dependencies](#7-step-5--install-dependencies)
8. [Step 6 — Tokenize the data](#8-step-6--tokenize-the-data)
9. [Step 7 — Run training](#9-step-7--run-training)
10. [Step 8 — Rescue the artifacts](#10-step-8--rescue-the-artifacts)
11. [Step 9 — Stop the instance and check the bill](#11-step-9--stop-the-instance-and-check-the-bill)
12. [What to do with the checkpoint](#12-what-to-do-with-the-checkpoint)
13. [Cost model](#13-cost-model)
14. [Troubleshooting](#14-troubleshooting)
15. [Appendix — copy-paste command sequence](#15-appendix--copy-paste-command-sequence)

---

## 1. Why a single 4090 is enough

The pipeline doc lists **1× RTX 4090-24GB as the minimum viable hardware** for Stage B (SFT), because Qwen3.5-0.8B is tiny (0.8B params, ~24 layers, hidden 1024). `training/train_sft.py` implements a memory recipe that fits a **full fine-tune** (not LoRA) in 24 GB:

| Component | VRAM |
|---|---|
| bf16 weights | ~1.6 GB |
| bf16 gradients | ~1.6 GB |
| `paged_adamw_8bit` optimizer state (bitsandbytes) | ~3.2 GB |
| Activations (batch 2 × 6,144 tokens, gradient checkpointing, flash-attn-2) | ~8–11 GB |
| **Peak** | **~14–18 GB** — comfortable headroom on 24 GB |

Expected wall clock: **~30–60 min for 3 epochs** with flash-attention-2 (~2× slower with the SDPA fallback). A `--lora` fallback flag (~12 GB, r=64 α=128 on all linear layers) exists for smaller cards, but on a 4090 always do the full FT — LoRA costs 3–6 points on gate A per the pipeline doc.

## 2. Prerequisites

**On Novita:**
- An account at [novita.ai](https://novita.ai) and credit topped up (GPU instances are prepaid from balance; a few dollars covers this whole exercise).
- **SSH public key uploaded *before* creating the instance.** Novita applies SSH keys at instance-creation time — keys added afterwards do not apply to already-created instances. Generate one locally and paste it under **Console → Settings → SSH Public Keys**:
  ```bash
  ssh-keygen -t rsa          # accept defaults
  ssh-add                     # load it into the agent
  cat ~/.ssh/id_rsa.pub       # copy this into the Novita console
  ```

**Locally / for artifacts:**
- `ssh`/`scp` (or `rsync`) in your terminal. On Windows, use WSL.
- A [Hugging Face](https://huggingface.co) account + a write-capable **access token** (Settings → Access Tokens) — used to download `Qwen/Qwen3.5-0.8B` and (recommended) to upload the trained checkpoint off the box.

**In the repo:** the built training batch must exist — `datasets/sft_trajectories.jsonl` (930 execution-verified trajectories). If not, rebuild first (CPU-only, no GPU needed):

```bash
python3 -m data_engine.build --n-sft 930 --n-routing 1240 --n-pref 240 --seed 2026
python3 -m data_engine.validate
```

## 3. Step 1 — Launch the instance

Per Novita's [Create Instances guide](https://docs.novita.ai/guides/gpu-instance-quickstart-create-instances):

1. Log in and go to **GPU Instance** (the **Explore** page lists available GPU types and data-center regions).
2. Pick **RTX 4090 (24 GB)**. Filter by region — pick one with stock and acceptable latency to you.
3. **Choose the billing mode:**
   - **On-demand** (~**$0.33–0.35/hr**, [third-party tracked](https://computeprices.com/providers/novita/gpus/rtx4090); verify the live price in the console) — **recommended for this job.** The run is under an hour, so interruption risk isn't worth the discount.
   - **Spot** (~**$0.17–0.18/hr**, up to 50% off) — only with checkpointed/resumable runs, since spot instances can be reclaimed mid-training. Our job is short and checkpoints every 200 steps, so spot is acceptable if you're cheap; on-demand removes the risk entirely.
4. **Pick a template/image.** Choose an official **PyTorch 2.x + CUDA 12.x** template. When configuring, **check the "Start Jupyter Notebook" option** — official templates with this checked come with JupyterLab preinstalled (per the [JupyterLab guide](https://docs.novita.ai/guides/gpu-instance-jupyterlab)). Pick a recent template: you need a transformers release new enough to know `Qwen3.5`.
5. **Configure the instance:**

   | Setting | Value | Why |
   |---|---|---|
   | GPU count | 1 | the run is single-GPU |
   | vCPU / memory | 8–16 vCPU, 32–64 GB | dataloader workers + tokenization; more is harmless |
   | Container disk | ≥ 60 GB | 60 GB/day is Novita's **free** storage quota; this also holds base model + checkpoints |
   | Volume (optional) | 20–50 GB | survives instance stop/delete — safest home for `runs/` (see [Step 8](#10-step-8--rescue-the-artifacts)) |
   | Exposed ports | `8888` (Jupyter), `22` (SSH is automatic) | comma-separated if adding more |
   | Environment variables | `HF_TOKEN=<your token>` | injected at container start; the HF CLI picks it up |

6. **Deploy.** Billing starts when the instance enters the **pulling** state (image download), not when you connect — don't let it idle.

## 4. Step 2 — Connect (SSH / JupyterLab)

**SSH (primary, needed for `scp`/`rsync`):** In **Console → Instances**, find the instance, click **Connect**, and copy the **Basic SSH Terminal** command into your local terminal. It looks like:

```bash
ssh root@<region>.novita.ai -p <port>
```

- If you uploaded your SSH key in Step 2 of Prerequisites, it just works.
- If not, the Connect popup shows the **root password** — you'll be prompted for it.
- **Immediately start `tmux`** after logging in. If your laptop sleeps or the SSH connection drops, tmux keeps the training alive:

  ```bash
  tmux new -s docslm     # detach: Ctrl-b d · reattach: tmux attach -t docslm
  ```

**JupyterLab (browsing/notebook alternative):** with the instance running, click **Connect** (bottom-right of the instance card) → **Connect to Jupyter Lab** — it opens the preinstalled JupyterLab in a new tab. Fine for inspection and plotting loss curves; do the actual long-running training inside tmux over SSH.

## 5. Step 3 — Verify the environment

Inside the instance (in tmux):

```bash
nvidia-smi                # must show "NVIDIA GeForce RTX 4090", 24564 MiB
nvcc --version            # CUDA toolkit version of the image
python3 -c "import torch; print(torch.__version__, torch.cuda.is_available(),
           torch.cuda.get_device_name(0))"
python3 -c "import transformers; print(transformers.__version__)"
```

If the template's `transformers` predates Qwen3.5, upgrade it (Step 5). Confirm the GPU is idle: `nvidia-smi` should show ~0 MiB used before you start.

## 6. Step 4 — Upload the repo and data

Only three things are needed on the box: `datasets/sft_trajectories.jsonl`, `training/`, and a tokenizer (downloaded in Step 5). From your **local** machine:

```bash
cd /home/nihal/Storage/Docskills/docslm
tar czf docslm-train.tar.gz datasets/sft_trajectories.jsonl training/
scp docslm-train.tar.gz root@<region>.novita.ai -P <port>:/root/
```

(SSH-with-key users can also use `rsync -avz -e "ssh -p <port>"`. Password users: `scp` will prompt.) Then on the instance:

```bash
cd /root && tar xzf docslm-train.tar.gz
```

## 7. Step 5 — Install dependencies

```bash
pip install -U "transformers>=4.51" datasets accelerate peft bitsandbytes "huggingface_hub[cli]"
```

**flash-attention-2** (the training script selects it whenever CUDA is available, and it roughly halves step time). Install the **prebuilt wheel matching your torch + CUDA versions** rather than compiling:

```bash
pip install flash-attn --no-build-isolation
```

If the build fails or drags on, either grab a matching wheel from the [flash-attention releases page](https://github.com/Dao-AILab/flash-attention/releases) or patch the fallback in `train_sft.py` (see [Troubleshooting](#14-troubleshooting) — SDPA works, just ~2× slower).

**Model + tokenizer download** (~2 GB, goes to `~/.cache/huggingface`):

```bash
hf auth login                     # or export HF_TOKEN=... (injected via instance env var)
hf download Qwen/Qwen3.5-0.8B
```

## 8. Step 6 — Tokenize the data

`prep_sft_data.py` renders each trajectory in **Qwen3's native chat format** (`<|im_start|>…` with `<think>` blocks and `<tool_call>` JSON) and masks loss to **assistant tokens only** — system/user/tool text becomes `-100`. This train/serve parity is non-negotiable (ADR-3).

```bash
python3 training/prep_sft_data.py \
    --data datasets/sft_trajectories.jsonl \
    --out datasets/sft_tokenized.jsonl \
    --max-len 6144
```

Read the output — it's the pre-flight check:

```
kept 930, skipped (>6144 tok): <n>
token lens: min=... p50=... p90=... max=... total=~2.5M (2.5M tokens/epoch)
assistant-token ratio (200-sample): ~25-40%
```

- `kept` should be 930 (or 930 − a handful of over-length skips).
- The assistant-token ratio confirms the loss mask works; a ratio near 100% would mean everything (including system prompts) is being trained on — a bug.
- Total ≈ 2.5M tokens/epoch matches the script's expected throughput numbers.

## 9. Step 7 — Run training

```bash
python3 training/train_sft.py \
    --data datasets/sft_tokenized.jsonl \
    --out runs/sft-v1
```

Defaults (already tuned for the 4090 — don't change without reason): **full FT**, 3 epochs, LR 1e-5 cosine with 3% warmup, batch 2 × grad-accum 16 (effective 32), bf16, gradient checkpointing, `paged_adamw_8bit`, checkpoints every 200 steps (2 kept), seed 2026.

**While it runs, in another pane:**

```bash
watch -n 5 nvidia-smi     # expect ~14-18 GB peak; >22 GB means trouble (see OOM below)
```

**What to expect:**
- Step time ~1–3 s/step with flash-attn → **30–60 min total** for the run.
- Loss should fall from ~2–3 toward <1.2 and keep descending smoothly. Because loss is only on assistant tokens, it reads higher than a naive whole-sequence loss would — that's correct.
- Checkpoints land in `runs/sft-v1/checkpoint-*`; the merged, ready-to-serve model in **`runs/sft-v1/final/`** (bf16 safetensors + tokenizer).

**Resume after interruption:** `Trainer` supports it, but the script has no `--resume` flag; for a <1 h job simply re-run from scratch. If you're on spot and want resumability, edit the final `.train()` call to `.train(resume_from_checkpoint=True)` (it auto-finds the latest `checkpoint-*` in `--out`).

**LoRA fallback** (only if something forces you below 24 GB): add `--lora` — the script merges and unloads adapters before saving, so `final/` is still a plain model.

## 10. Step 8 — Rescue the artifacts

> ⚠️ **This is the step people skip and regret.** On Novita, the **container disk is ephemeral**: when you stop (or the provider reclaims) the instance you lose anything not on a **Volume**. Billing-relevant storage: container disk $0.005/GB/day (first 60 GB free), volume $0.005/GB/day, network volume $0.002/GB/day.

`runs/sft-v1/final` is ~2–3 GB (bf16). Get it off the container, in order of preference:

**A. Push to Hugging Face (recommended — survives everything, ~2 min):**

```bash
hf auth whoami                                   # confirm the write token works
hf upload <your-name>/docslm-sft-v1 runs/sft-v1/final --repo-type model
```

**B. `scp` back to your machine** (from your *local* terminal):

```bash
scp -r -P <port> root@<region>.novita.ai:/root/runs/sft-v1/final ./runs/sft-v1/
```

**C. Copy to a Volume** you attached at creation time — it persists across stop/start:

```bash
cp -r runs/sft-v1/final /root/volume/docslm/sft-v1-final
```

Also copy the **lineage record**: the console output of Steps 6–7 (token counts, final loss, `trainable params` line, seed) into a small `runs/sft-v1/RUN_NOTES.md` before pushing — the pipeline doc's reproducibility contract (seed + manifest hash + env digests per run) starts here.

## 11. Step 9 — Stop the instance and check the bill

In **Console → Instances → Stop** (don't just disconnect SSH — a running instance bills).

Billing mechanics (from Novita's [pricing doc](https://docs.novita.ai/guides/gpu-instance-pricing)):

- **Compute** = unit price × duration × GPU count, **metered per second, settled hourly**, from instance creation (pulling state) until stop.
- **Storage** bills per GB per day while data exists (container disk 60 GB free quota).

Realistic run total: 1.5–2 h of 4090 on-demand ≈ **$0.50–0.70**, plus cents of storage. Delete the instance only after your checkpoint is confirmed off-box.

## 12. What to do with the checkpoint

`runs/sft-v1/final` is the **Stage B output**. Per the pipeline it feeds forward:

1. **Smoke-eval locally** (CPU is fine for 0.8B): load with `transformers`, run 3–5 create-route prompts from the held-out sample, confirm the model emits well-formed `<tool_call>` JSON and grounded `<think>` blocks — the SFT pilot gate is exec ≥ 70% (full DocBench in [05 — Evaluation](05_EVALUATION.md)).
2. **Stage C — DPO** on the 240 preference pairs in `datasets/preference_pairs.jsonl` (β = 0.1, LR 5e-7, 1 epoch) — another single-4090-sized job; reuse this exact runbook with the DPO trainer.
3. **Stage D — quantize**: GGUF Q4_K_M via llama.cpp (~0.5 GB), gate B must hold within −2 pts. Serving/exports in [06 — Deployment](06_DEPLOYMENT.md).

## 13. Cost model

| Item | Rate (verify live in console) | This job |
|---|---|---|
| RTX 4090 on-demand | ~$0.33–0.35/GPU-hr | 1.5–2 h ≈ **$0.50–0.70** |
| RTX 4090 spot | ~$0.17–0.18/GPU-hr | ~half the above, preemption risk |
| Container disk | $0.005/GB/day, 60 GB free | $0 (under quota) |
| Volume | $0.005/GB/day | 30 GB held 1 week ≈ $1.05 |
| Network volume | $0.002/GB/day | cheapest persistence option |

Scale reference: even the full-scale Stage B from the pipeline doc (60k trajectories, ~1.1B tokens) is ~a few hundred 4090-hours ≈ **$100–150** on-demand — still trivially cheap; data, not compute, is the budget center.

## 14. Troubleshooting

| Symptom | Cause → fix |
|---|---|
| `ValueError: FlashAttention2 has been requested but flash-attn ... not installed` | Template lacks flash-attn → install the prebuilt wheel (Step 5), or change `attn_implementation` in `train_sft.py` to `"sdpa"` (correct result, ~2× slower) |
| CUDA OOM | Peak > 24 GB → set `--batch 1 --accum 32` (same effective batch); if still OOM, add `--lora`; check nothing else holds VRAM (`nvidia-smi`) |
| `Permission denied (publickey)` on SSH | Keys added *after* instance creation don't apply, key not loaded (`ssh-add`), or wrong permissions on the key file → use the password from the Connect popup, or recreate the instance with keys in place; `ssh -vvv` to debug |
| Instance unreachable after idle | Some templates/services stop; hard-check via console status, restart if needed — and use **tmux** so this never kills a run |
| `hf download` 401/403 | `HF_TOKEN` not set / expired → `hf auth login` interactively |
| `transformers` doesn't recognize `Qwen/Qwen3.5-0.8B` | Template too old → `pip install -U transformers`, restart the Python process |
| Tokenizer download slow | Use the `HF_HUB_ENABLE_HF_TRANSFER=1` env var (`pip install hf_transfer`) |
| Spot instance reclaimed mid-run | Checkpoints every 200 steps are in `runs/sft-v1/` (container disk — lost on reclaim!) → re-launch with a **Volume** and `--out /root/volume/runs/sft-v1`, add `resume_from_checkpoint=True` |
| Training seems stalled at step 0 | First steps compile/allocate; give it 2–3 min, check `nvidia-smi` shows the python process before assuming the worst |

## 15. Appendix — copy-paste command sequence

```bash
# ── local ────────────────────────────────────────────────────────────────
ssh-keygen -t rsa && ssh-add && cat ~/.ssh/id_rsa.pub     # paste into Novita console
cd /home/nihal/Storage/Docskills/docslm
python3 -m data_engine.build --n-sft 930 --n-routing 1240 --n-pref 240 --seed 2026
python3 -m data_engine.validate
tar czf docslm-train.tar.gz datasets/sft_trajectories.jsonl training/
scp docslm-train.tar.gz root@<host> -P <port>:/root/
# ... launch instance in Novita console (4090, PyTorch/CUDA12 template, Jupyter on) ...

# ── on the instance (inside tmux) ────────────────────────────────────────
tmux new -s docslm
cd /root && tar xzf docslm-train.tar.gz
pip install -U "transformers>=4.51" datasets accelerate peft bitsandbytes "huggingface_hub[cli]"
pip install flash-attn --no-build-isolation
hf auth login && hf download Qwen/Qwen3.5-0.8B
nvidia-smi && python3 -c "import torch;print(torch.cuda.get_device_name(0))"

python3 training/prep_sft_data.py --data datasets/sft_trajectories.jsonl \
    --out datasets/sft_tokenized.jsonl --max-len 6144
python3 training/train_sft.py --data datasets/sft_tokenized.jsonl --out runs/sft-v1
# (~30-60 min; watch nvidia-smi in another pane)

hf upload <your-name>/docslm-sft-v1 runs/sft-v1/final --repo-type model
# ── then: Console → Instances → Stop ─────────────────────────────────────
```

---

## Sources

- [Novita AI — GPU Instance Overview](https://docs.novita.ai/guides/gpu-instance-overview)
- [Novita AI — Create Instances (Quickstart)](https://docs.novita.ai/guides/guides-quickstart-create-instance) / [Preparations](https://docs.novita.ai/guides/gpu-instance-quickstart-preparations)
- [Novita AI — Connect to Instance (SSH)](https://docs.novita.ai/guides/gpu-instance-quickstart-connect-to-instance)
- [Novita AI — JupyterLab](https://docs.novita.ai/guides/gpu-instance-jupyterlab)
- [Novita AI — GPU Instance Pricing](https://docs.novita.ai/guides/gpu-instance-pricing)
- [Novita AI GPU Cloud](https://novita.ai/gpus) · [Pricing hub](https://novita.ai/pricing)
- RTX 4090 price tracking: [ComputePrices](https://computeprices.com/providers/novita/gpus/rtx4090) · [UsagePricing](https://www.usagepricing.com/tools/pricing-calculator/novita-ai) (approximate third-party figures — the console price is authoritative)
- In-repo: [04 — Training Pipeline](04_TRAINING_PIPELINE.md) · [07 — Datasets](07_DATASETS.md) · [06 — Deployment](06_DEPLOYMENT.md) · `training/train_sft.py` · `training/prep_sft_data.py`
