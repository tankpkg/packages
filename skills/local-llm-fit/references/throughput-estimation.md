# Throughput Estimation — Predicting Tokens Per Second

Sources: llama.cpp benchmark discussions, Apple MLX benchmarks, vLLM performance docs, NVIDIA Nsight profiling notes, r/LocalLLaMA community benchmarks (2023–2026), memory-bandwidth-bound inference analyses.

Covers: why decode is bandwidth-bound, the ceiling formula, prompt vs decode, engine multipliers, MoE throughput, thermal sustained vs peak, and batch effects.

## 1. Why Decode Is Bandwidth-Bound, Not Compute-Bound

Single-user, batch=1 decode reads every active weight from memory once per token. Arithmetic is negligible compared to bytes moved. Therefore:

```
tok/s (ceiling) ≈ memory_bandwidth_GBs / active_weight_bytes_per_token
```

`active_weight_bytes_per_token` is the size of the weights the model actually reads for one token:
- Dense model: full weight size in GB.
- MoE: active params × bytes/param (not total).

This single formula explains ~80% of observed throughput.

## 2. Memory Bandwidth Cheat Sheet

Peak advertised bandwidth, in GB/s. Real sustained is 70–90% of peak.

| Hardware | Peak GB/s | Effective GB/s |
| --- | --- | --- |
| RTX 3060 12 GB | 360 | ~290 |
| RTX 3080 10 GB | 760 | ~610 |
| RTX 3090 24 GB | 936 | ~750 |
| RTX 4060 Ti 16 GB | 288 | ~230 |
| RTX 4070 12 GB | 504 | ~400 |
| RTX 4070 Ti Super 16 GB | 672 | ~540 |
| RTX 4080 16 GB | 717 | ~575 |
| RTX 4090 24 GB | 1008 | ~800 |
| RTX 5080 16 GB | ~960 | ~770 |
| RTX 5090 32 GB | ~1792 | ~1430 |
| AMD 7900 XTX 24 GB | 960 | ~720 |
| Apple M1 | 68 | ~55 |
| Apple M1 Pro | 200 | ~160 |
| Apple M1 Max | 400 | ~320 |
| Apple M1 Ultra | 800 | ~640 |
| Apple M2 / M2 Pro | 100 / 200 | ~80 / 160 |
| Apple M2 Max | 400 | ~320 |
| Apple M2 Ultra | 800 | ~640 |
| Apple M3 / M3 Pro | 100 / 150 | ~80 / 120 |
| Apple M3 Max (16c GPU) | 300 | ~240 |
| Apple M3 Max (40c GPU) | 400 | ~320 |
| Apple M3 Ultra | 800 | ~640 |
| Apple M4 / M4 Pro | 120 / 273 | ~100 / 220 |
| Apple M4 Max | 546 | ~440 |
| DDR5-6400 dual channel (CPU) | 102 | ~70 |
| DDR5-5600 dual channel | 90 | ~65 |
| DDR4-3200 dual channel | 51 | ~38 |
| Xeon/EPYC 8-channel DDR5 | 400–460 | ~320 |

Apple unified memory is shared with CPU and display. Subtract a few percent for real workloads.

## 3. Predicted Tok/s — Worked Numbers

Formula: `tok/s ≈ effective_bandwidth / weight_size_GB`.

### Llama-3.1-8B dense at Q4_K_M (4.9 GB active)

| Hardware | Effective GB/s | Predicted | Observed typical |
| --- | --- | --- | --- |
| RTX 3090 | 750 | 153 | 120–160 |
| RTX 4090 | 800 | 163 | 130–170 |
| RTX 4070 | 400 | 82 | 65–90 |
| M2 Pro | 160 | 33 | 25–38 |
| M3 Max 40c | 320 | 65 | 55–75 |
| M4 Max | 440 | 90 | 70–100 |
| CPU DDR5-6400 | 70 | 14 | 9–14 |

### Qwen2.5-32B dense at Q4_K_M (19.5 GB)

| Hardware | Effective GB/s | Predicted |
| --- | --- | --- |
| RTX 3090 (fits tightly) | 750 | 38 |
| RTX 4090 | 800 | 41 |
| M3 Max 40c | 320 | 16 |
| M2 Ultra | 640 | 33 |

### Llama-3.1-70B at Q4_K_M (42.7 GB) — needs 48 GB+

| Hardware | Effective GB/s | Predicted |
| --- | --- | --- |
| 2× RTX 3090 (NVLink) | ~600 effective | 14 |
| 2× RTX 4090 (PCIe) | ~650 effective | 15 |
| A6000 48 GB | ~650 | 15 |
| M2 Ultra 192 GB | 640 | 15 |
| M3 Ultra | 640 | 15 |
| M4 Max 128 GB (fp4-ish via Q4) | 440 | 10 |

### MoE: Qwen3-Next-80B-A3B — 80 GB in RAM, 3B active

Active weight size at Q4: `3 × 0.61 = 1.83 GB`.

| Hardware | Predicted |
| --- | --- |
| M2 Ultra 192 GB | 640 / 1.83 ≈ 350 |
| M4 Max 128 GB | 440 / 1.83 ≈ 240 |
| 2× RTX 4090 | 800 / 1.83 ≈ 430 |

Note: MoE routing adds overhead; realistic numbers are often 40–70% of these predictions for single-stream decode. Still very fast.

### MoE: DeepSeek-V3 / R1 — 671 GB total, 37B active

Needs ≥180 GB usable memory even at Q2. At Q4 (420 GB): requires a high-end workstation (M3/M4 Ultra 512 GB, multi-GPU server, EPYC with huge RAM).
Active 37B × Q4 = 22.6 GB per token.

| Hardware | Predicted |
| --- | --- |
| EPYC 12-channel DDR5 (~460 GB/s) | ~20 |
| H100 SXM (3.35 TB/s) if it fit | ~150 |

## 4. Prompt vs Decode

- **Prompt (prefill)** is compute-bound, not bandwidth-bound. It processes all input tokens in parallel. Prompt speed scales with FLOPs and with quantization efficiency (FP16 > Q8 > Q4 for compute), but is usually many multiples of decode speed.
- **Decode** is the bandwidth-bound number everyone quotes.

Typical ratio on GPUs: prompt ≈ 10–30× decode. On CPUs: 2–5× decode. Report both when relevant (long-prompt workloads care).

## 5. Engine Multipliers

Same model, same hardware, different engine → different tok/s. Rough multipliers relative to the bandwidth ceiling:

| Engine | Decode efficiency | Notes |
| --- | --- | --- |
| llama.cpp (CUDA) | 0.75–0.90 | Mature, close to ceiling |
| llama.cpp (Metal, MLX kernels) | 0.70–0.85 | Apple, very close to MLX |
| Ollama | 0.75–0.90 | Wraps llama.cpp |
| MLX | 0.80–0.90 | Apple native, best on M-series |
| ExLlamaV2 | 0.85–0.95 | Fastest single-GPU for GPTQ/EXL2 |
| vLLM (batch=1) | 0.60–0.80 | Overhead; shines at batched serving |
| TensorRT-LLM | 0.85–0.95 | Enterprise, complex setup |
| Transformers + bnb | 0.30–0.50 | Slow; use only if no alternative |

## 6. Thermal / Sustained vs Peak

Peak tok/s is what you see for the first few seconds. Sustained (long-running) tok/s is what matters for real use.

| Device class | Peak → sustained drop |
| --- | --- |
| Desktop GPU, good cooling | 0–10% |
| Desktop GPU, stock air | 5–15% |
| Laptop GPU (dGPU) | 15–40% |
| MacBook (Pro cooling) | 10–25% |
| MacBook Air (passive) | 30–60% |
| Mac Studio / Mac Pro | 0–10% |

On battery, Apple laptops clock the GPU lower; expect 30–50% of wall-power tok/s. Call this out in the report when hardware is a laptop.

## 7. Batch Size and Parallelism

At batch=1, the formula above holds. As batch grows, memory-bandwidth is amortized across requests and effective per-request tok/s rises until compute becomes the bottleneck. For a single-user local setup, assume batch=1. For serving, vLLM and TensorRT-LLM dominate.

## 8. When Prediction Diverges From Reality

If the user reports observed tok/s much lower than the formula predicts, the usual culprits:

| Gap | Likely cause |
| --- | --- |
| 2–5× too slow | Model not actually on GPU (partial offload, VRAM full). Check layer offload count. |
| 1.5–2× too slow | Context full, KV cache thrashing. |
| 30–50% too slow | Thermal throttle; check sustained load. |
| Any | Wrong engine (Transformers + bnb), or prompt eval mis-measured as decode. |

## 9. Minimum Acceptable Tok/s

Calibrated expectations:

| Use case | Comfortable | Tolerable | Painful |
| --- | --- | --- | --- |
| Interactive chat | ≥15 | 8–15 | <8 |
| Coding autocomplete (streaming) | ≥25 | 15–25 | <15 |
| Batch summarization | ≥5 | 2–5 | <2 |
| Agent loops (many turns) | ≥20 | 10–20 | <10 |

Tie this to the verdict rubric in SKILL.md. Sub-5 tok/s decode on a single-user interactive model = ❌ regardless of fit.

## 10. Report-Ready Sentence

When stating throughput, include:
- The formula inputs (bandwidth, active-weight GB)
- The engine assumed
- Peak vs sustained if the hardware is a laptop

Example:
> "On your M3 Pro (≈120 GB/s effective, MLX, active weights ~4.9 GB), decode will run at ~24 tok/s peak and ~20 tok/s sustained on battery. Prompt prefill ~250 tok/s."
