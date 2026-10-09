# =============================================================================
# DocSLM training image for Novita AI GPU instances
#
# Purpose: bake everything train.sh would otherwise install at runtime into a
# single image, so an instance boots ready-to-train (deps + flash-attn + model).
#
# Base image rule (see docs/08_NOVITA_4090_TRAINING.md):
#   * RTX 5090 (Blackwell): CUDA >= 12.8 required (cu128/cu129/cu130 builds)
#   * RTX 4090 (Ada):       any CUDA 12.x works
#   * Always the -devel variant: ships nvcc so flash-attn can compile from
#     source when no prebuilt wheel matches.
#
# Build & push:
#   docker build -t <dockerhub-user>/docslm-train:latest .
#   docker push <dockerhub-user>/docslm-train:latest
# Then in the Novita console: GPU Instance -> Custom Image -> <dockerhub-user>/docslm-train:latest
# (private images: enter your Docker Hub credentials when creating the instance)
#
# NOTE: no ENTRYPOINT/CMD here on purpose — inheriting the base image's keeps
# Novita's SSH / "Start Jupyter Notebook" integration working.
# =============================================================================

# Pin to the exact base you validated on the working instance — the preflight
# line "torch 2.9.0+cu129" tells you what to match. Override at build time with:
#   docker build --build-arg BASE_IMAGE=novitalabs/pytorch:<tag> .
ARG BASE_IMAGE=novitalabs/pytorch:2.9.0-cuda12.9-cudnn9-devel
FROM ${BASE_IMAGE}

ARG MODEL_ID=Qwen/Qwen3.5-0.8B

LABEL org.opencontainers.image.title="docslm-train" \
      org.opencontainers.image.description="DocSLM-0.8B SFT training image (torch + CUDA 12.9 + flash-attn + HF stack)" \
      org.opencontainers.image.licenses="Apache-2.0"

# fast Hugging Face downloads (hf_transfer); keep the model cache in /workspace
# so it lands on the container disk you can back up
ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    PYTHONUNBUFFERED=1 \
    HF_HUB_ENABLE_HF_TRANSFER=1 \
    HF_HOME=/workspace/hf

# ---- system packages (mirrors what train.sh would apt-install) --------------
RUN apt-get update -qq \
 && apt-get install -y -qq --no-install-recommends \
      git tmux curl rsync ca-certificates build-essential less vim \
 && rm -rf /var/lib/apt/lists/*

# ---- Python stack ------------------------------------------------------------
# torch itself is NOT installed here: the base image's build is CUDA-matched.
# transformers must be new enough to know the qwen3_5 architecture (Qwen3.5,
# Mar 2026) — 4.x releases predate it, hence the 5.x-era floor.
RUN pip install --no-cache-dir -U \
      "transformers>=5.19" \
      datasets \
      accelerate \
      peft \
      bitsandbytes \
      huggingface_hub \
      hf_transfer \
      ninja \
      jupyterlab \
 && python3 -c "from transformers.models.auto.configuration_auto import CONFIG_MAPPING; assert 'qwen3_5' in CONFIG_MAPPING"

# ---- flash-attention ----------------------------------------------------------
# Prebuilt wheels are torch-version specific; 2.8.3 covers torch 2.9 on
# CUDA 12 for py3.10–3.14. --no-build-isolation lets it see the base image's
# torch at build time. If this ever falls back to a source build it needs the
# nvcc from the -devel base (that's why we use it).
RUN pip install --no-cache-dir flash-attn==2.8.3 --no-build-isolation \
 || echo "WARNING: flash-attn build failed — train.sh will use SDPA (set FLASH_ATTN=skip)"

# ---- optional Qwen3.5 kernel accelerators ------------------------------------
# Qwen3.5 mixes linear-attention (gated delta rule) and short-conv layers;
# without these kernels transformers uses correct-but-slower reference impls
RUN pip install --no-cache-dir flash-linear-attention \
 || echo "WARNING: flash-linear-attention unavailable — reference kernels will be used"
RUN pip install --no-cache-dir causal-conv1d \
 || echo "WARNING: causal-conv1d unavailable — reference kernels will be used"

# ---- pre-bake the base model (~2 GB) -----------------------------------------
# Saves the per-instance download; every launch starts with a warm HF cache.
# Delete this RUN if you'd rather keep the image slim.
RUN hf download "${MODEL_ID}"

WORKDIR /workspace
# login-shell convenience: print GPU + torch/CUDA build on SSH login
RUN printf '%s\n' \
    'nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || true' \
    'python3 -c "import torch; print(\"torch\", torch.__version__, \"+cuda\", torch.version.cuda)" 2>/dev/null || true' \
    > /etc/profile.d/00-gpu-info.sh
