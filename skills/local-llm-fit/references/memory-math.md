# Memory Math — Weights, KV Cache, Overhead

Sources: llama.cpp quantization docs, ExLlamaV2 docs, MLX docs, Hugging Face Transformers memory guides, community benchmarks (r/LocalLLaMA, HF spaces), NVIDIA Nsight profiles.

Covers: bytes-per-parameter by format, KV cache per-architecture formulas, MoE active vs total, context-length scaling, and the overhead budget. All numbers are practical, not theoretical.

## 1. The Fit Equation

```
memory_required = weights_bytes
                + kv_cache_bytes(ctx, batch)
                + activations_bytes
                + engine_overhead_bytes
```

Rule of thumb for engine overhead + activations (batch=1, typical decode):
- llama.cpp / Ollama (CPU or GPU): 0.3–0.8 GB
- MLX: 0.3–0.6 GB
- vLLM: 1.0–2.0 GB (CUDA graphs, paged KV)
- ExLlamaV2: 0.5–1.0 GB
- Transformers + bitsandbytes: 1.5–2.5 GB (less efficient)

Use 1 GB as a safe default when you can't measure.

## 2. Bytes Per Parameter

The single most-used table in this skill. Multiply by parameter count (in billions) to get weight size in GB.

### GGUF (llama.cpp / Ollama)

| Quant | Bits (avg) | Bytes/param | 7B | 13B | 34B | 70B |
| --- | --- | --- | --- | --- | --- | --- |
| F32 | 32 | 4.00 | 28.0 | 52.0 | 136 | 280 |
| F16 / BF16 | 16 | 2.00 | 14.0 | 26.0 | 68.0 | 140 |
| Q8_0 | 8.5 | 1.06 | 7.4 | 13.8 | 36.1 | 74.2 |
| Q6_K | 6.56 | 0.82 | 5.7 | 10.7 | 27.9 | 57.4 |
| Q5_K_M | 5.68 | 0.71 | 5.0 | 9.2 | 24.1 | 49.7 |
| Q5_K_S | 5.52 | 0.69 | 4.8 | 9.0 | 23.5 | 48.3 |
| Q5_0 | 5.5 | 0.69 | 4.8 | 9.0 | 23.5 | 48.3 |
| Q4_K_M | 4.84 | 0.61 | 4.2 | 7.9 | 20.6 | 42.4 |
| Q4_K_S | 4.58 | 0.57 | 4.0 | 7.5 | 19.5 | 40.1 |
| Q4_0 | 4.55 | 0.57 | 4.0 | 7.4 | 19.3 | 39.8 |
| Q3_K_M | 3.91 | 0.49 | 3.4 | 6.4 | 16.6 | 34.2 |
| Q3_K_S | 3.50 | 0.44 | 3.1 | 5.7 | 14.9 | 30.6 |
| Q2_K | 3.35 | 0.42 | 2.9 | 5.5 | 14.2 | 29.3 |
| IQ3_XXS | 3.06 | 0.38 | 2.7 | 5.0 | 13.0 | 26.8 |
| IQ2_XS | 2.31 | 0.29 | 2.0 | 3.8 | 9.8 | 20.2 |
| IQ2_XXS | 2.06 | 0.26 | 1.8 | 3.4 | 8.8 | 18.0 |
| IQ1_S | 1.56 | 0.20 | 1.4 | 2.5 | 6.6 | 13.6 |

**Quality ranking** (practical, not formal):
F16 ≈ Q8_0 > Q6_K > Q5_K_M > Q4_K_M > Q4_0 > Q3_K_M > Q2_K > IQ1_*

Below Q3 the model noticeably degrades. `Q4_K_M` is the default sweet spot.

### EXL2 (ExLlamaV2, GPU)

Variable-bit quantization. Repo names carry the bpw (bits per weight).

| bpw | Bytes/param | 7B | 13B | 34B | 70B |
| --- | --- | --- | --- | --- | --- |
| 8.0 | 1.00 | 7.0 | 13.0 | 34.0 | 70.0 |
| 6.0 | 0.75 | 5.3 | 9.8 | 25.5 | 52.5 |
| 5.0 | 0.63 | 4.4 | 8.1 | 21.3 | 43.8 |
| 4.65 | 0.58 | 4.1 | 7.6 | 19.8 | 40.7 |
| 4.25 | 0.53 | 3.7 | 6.9 | 18.1 | 37.2 |
| 4.0 | 0.50 | 3.5 | 6.5 | 17.0 | 35.0 |
| 3.5 | 0.44 | 3.1 | 5.7 | 14.9 | 30.6 |
| 3.0 | 0.38 | 2.6 | 4.9 | 12.8 | 26.3 |
| 2.4 | 0.30 | 2.1 | 3.9 | 10.2 | 21.0 |

EXL2 4.65bpw is the common sweet spot for single-GPU rigs.

### MLX (Apple Silicon)

| Quant | Bits | Bytes/param | 7B | 13B | 34B | 70B |
| --- | --- | --- | --- | --- | --- | --- |
| fp16 | 16 | 2.00 | 14.0 | 26.0 | 68.0 | 140 |
| 8-bit | 8 | 1.00 | 7.0 | 13.0 | 34.0 | 70.0 |
| 6-bit | 6 | 0.75 | 5.3 | 9.8 | 25.5 | 52.5 |
| 4-bit | 4 | 0.50 | 3.5 | 6.5 | 17.0 | 35.0 |
| 3-bit | 3 | 0.38 | 2.6 | 4.9 | 12.8 | 26.3 |

### AWQ / GPTQ / bitsandbytes

| Format | Bits | Bytes/param | Notes |
| --- | --- | --- | --- |
| AWQ 4-bit | 4 | 0.50 | + ~5% scale tensors; GPU only |
| AWQ 8-bit | 8 | 1.00 | Rare |
| GPTQ 4-bit | 4 | 0.50 | group_size 128 typical; GPU only |
| bnb nf4 | 4 | 0.50 | Transformers path, slow inference |
| bnb fp4 | 4 | 0.50 | Similar |
| bnb int8 | 8 | 1.00 | Transformers path |
| FP8 (E4M3/E5M2) | 8 | 1.00 | Hopper/Ada only; vLLM, TensorRT-LLM |

## 3. KV Cache — The Hidden Memory Eater

KV cache scales linearly with context tokens. At long context, it can rival the weights.

### Exact Formula

```
kv_cache_bytes = 2 (K+V)
               * num_layers
               * num_kv_heads   ← GQA: kv_heads < attn_heads
               * head_dim
               * dtype_bytes    ← usually 2 (FP16), sometimes 1 (KV-quant 8-bit)
               * ctx_tokens
               * batch_size
```

`num_kv_heads` matters. Modern models use Grouped Query Attention (GQA) or Multi-Query Attention (MQA), which drastically shrinks KV. Older models without GQA (e.g. Llama 1, early Falcon) have painfully large KV caches.

### Common Models — KV Per Token (FP16, batch=1)

| Model | layers | kv_heads | head_dim | KB/token |
| --- | --- | --- | --- | --- |
| Llama-2-7B | 32 | 32 | 128 | 512 |
| Llama-2-13B | 40 | 40 | 128 | 800 |
| Llama-2-70B | 80 | 8 | 128 | 320 |
| Llama-3-8B | 32 | 8 | 128 | 128 |
| Llama-3-70B | 80 | 8 | 128 | 320 |
| Llama-3.1-8B | 32 | 8 | 128 | 128 |
| Llama-3.1-70B | 80 | 8 | 128 | 320 |
| Qwen2.5-7B | 28 | 4 | 128 | 56 |
| Qwen2.5-14B | 48 | 8 | 128 | 192 |
| Qwen2.5-32B | 64 | 8 | 128 | 256 |
| Qwen2.5-72B | 80 | 8 | 128 | 320 |
| Mistral-7B | 32 | 8 | 128 | 128 |
| Mixtral-8x7B | 32 | 8 | 128 | 128 |
| Gemma-2-9B | 42 | 8 | 256 | 336 |
| Gemma-2-27B | 46 | 16 | 128 | 368 |
| Phi-3-medium (14B) | 40 | 10 | 128 | 200 |
| DeepSeek-V2 (MLA) | 60 | — | — | ~70 (MLA) |
| DeepSeek-V3 (MLA) | 61 | — | — | ~70 (MLA) |

MLA (Multi-head Latent Attention) in DeepSeek-V2/V3/R1 compresses KV aggressively — roughly 7× smaller than standard GQA at the same params. It is a big reason DeepSeek-class MoE is runnable at long context on modest hardware.

### KV at Different Contexts

Multiply KB/token × ctx_tokens / 1_048_576 → GB.

Example: Llama-3.1-70B at 16k context:
`320 KB × 16384 / 1024 / 1024 = 5.0 GB` KV cache alone, on top of weights.

### KV Quantization

Llama.cpp supports KV cache in 8-bit (halves KV memory) and 4-bit (quarters it, some quality loss). Flag: `-ctk q8_0 -ctv q8_0`. Use this when context is the bottleneck.

## 4. MoE — Active vs Total

For Mixture-of-Experts models, **weights in memory = total params**, but **compute per token ≈ active params**.

| Model | Total | Active | Active fraction |
| --- | --- | --- | --- |
| Mixtral-8x7B | ~47B | ~13B | 0.28 |
| Mixtral-8x22B | ~141B | ~39B | 0.28 |
| Qwen3-Next-80B-A3B | 80B | 3B | 0.04 |
| DeepSeek-V3 | 671B | 37B | 0.055 |
| DeepSeek-R1 | 671B | 37B | 0.055 |

Implications:
- **Memory footprint:** use total params × bytes/param.
- **Throughput:** use active params for the bandwidth calculation in `throughput-estimation.md`. This is why an 80B/A3B MoE can be faster than a 13B dense model if you have the RAM.

## 5. Overhead Budget

Don't plan to fill memory to 100%. Leave headroom.

| Platform | Safe target | Reason |
| --- | --- | --- |
| Discrete GPU (dedicated) | 90% of VRAM | Desktop compositor, other apps |
| Discrete GPU (daily driver) | 80% of VRAM | Browser, IDE can spike VRAM |
| Apple Silicon unified | 70% of total RAM | macOS pages aggressively; large apps |
| CPU-only (dedicated box) | 80% of RAM | OS, buffers |
| CPU-only (workstation) | 60% of RAM | You still need your other apps |

On Apple, `sudo sysctl iogpu.wired_limit_mb=<mb>` raises the default ~67%/75% wired-VRAM cap. Document this when recommending a large MLX model on a 64/128/192 GB Mac.

## 6. Worked Example — Llama-3.1-70B on a 4090 (24 GB)

Target: 8k context, batch=1, llama.cpp.

```
Weights Q4_K_M:   70 × 0.61  = 42.7 GB  ← won't fit alone
Weights Q3_K_M:   70 × 0.49  = 34.3 GB  ← still won't fit
Weights IQ2_XXS:  70 × 0.26  = 18.2 GB  ← fits, but quality drops
KV @ 8k FP16:     320 × 8192 / 1024^2 = 2.5 GB
KV @ 8k Q8_0:     1.25 GB
Overhead:         0.8 GB
Total IQ2_XXS:    18.2 + 1.25 + 0.8 = 20.25 GB  ← fits in 24 GB ✅
```

Verdict: runs with IQ2_XXS at ~8k ctx, quality noticeably lower than Q4. For comfortable Q4, you need two 24 GB GPUs or one 48 GB card.

## 7. Worked Example — Qwen2.5-14B on M2 Pro 16 GB

Target: 8k context, MLX.

```
Weights 4-bit:    14 × 0.50 = 7.0 GB
KV @ 8k FP16:     192 × 8192 / 1024^2 = 1.5 GB
Overhead:         0.5 GB
Total:            9.0 GB
Safe budget:      16 × 0.70 = 11.2 GB
```

Fits comfortably. At 6-bit: 10.5 + 1.5 + 0.5 = 12.5 GB → tight, reduce context to 4k.

## 8. Quick Sanity Numbers

When you just need a ballpark, use these:

- Dense model, Q4_K_M, 8k ctx: `~0.7 × B + 2 GB` where B is params in billions.
- Dense model, Q8_0, 8k ctx: `~1.2 × B + 2 GB`.
- MoE model, Q4_K_M, 8k ctx: same formula but B = total params.

Always follow up with the real numbers from §2–§4.
