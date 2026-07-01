# Hardware Profiles — Baselines for Fit and Throughput

Sources: NVIDIA/AMD datasheets, Apple Silicon specs, vendor release notes, community-measured tok/s (r/LocalLLaMA, LocalLLM benchmark repos), llama.cpp and MLX bench tables.

Covers: VRAM and bandwidth per GPU tier, Apple Silicon by chip, AMD and Intel GPUs, CPU-only inference, dual-GPU rigs, and what each tier can realistically run.

## 1. NVIDIA Consumer GPUs

| GPU | VRAM | Bandwidth (GB/s) | Realistic use |
| --- | --- | --- | --- |
| RTX 3060 12 GB | 12 | 360 | 7–8B Q4/Q5, 13B Q4 tight |
| RTX 3070 | 8 | 448 | 7–8B Q4_K_M only |
| RTX 3080 10 GB | 10 | 760 | 7–8B Q5/Q6, 13B Q4 tight |
| RTX 3080 12 GB | 12 | 912 | 7–8B Q6, 13B Q4_K_M |
| RTX 3090 | 24 | 936 | 13B FP16, 34B Q4, 70B Q2 |
| RTX 4060 8 GB | 8 | 272 | 3–4B FP16, 7B Q4 only |
| RTX 4060 Ti 16 GB | 16 | 288 | 13B Q8, 34B Q3 |
| RTX 4070 | 12 | 504 | 7–8B Q6, 13B Q4_K_M |
| RTX 4070 Super | 12 | 504 | Same as 4070, faster compute |
| RTX 4070 Ti | 12 | 504 | 7–8B Q8, 13B Q4_K_M |
| RTX 4070 Ti Super 16 GB | 16 | 672 | 13B Q8, 34B Q3 |
| RTX 4080 | 16 | 717 | 13B Q8, 34B Q3 |
| RTX 4080 Super | 16 | 736 | Same tier |
| RTX 4090 | 24 | 1008 | 13B FP16, 34B Q5, 70B Q2 |
| RTX 5070 | 12 | 672 | 7–8B Q8, 13B Q4_K_M |
| RTX 5070 Ti | 16 | 896 | 13B Q8, 34B Q4 tight |
| RTX 5080 | 16 | 960 | 13B Q8, 34B Q4 tight |
| RTX 5090 | 32 | 1792 | 34B Q8, 70B Q3/Q4 |

Laptop variants: typically 60–75% of desktop bandwidth. Laptop RTX 4090 has 16 GB VRAM and ~576 GB/s, not 24/1008. Always clarify desktop vs mobile.

## 2. NVIDIA Workstation / Data Center

| GPU | VRAM | Bandwidth | Notes |
| --- | --- | --- | --- |
| A4000 | 16 | 448 | Similar to 3070 with more VRAM |
| A5000 | 24 | 768 | Near-3090 |
| A6000 | 48 | 768 | 70B Q4_K_M single-GPU |
| RTX 6000 Ada | 48 | 960 | 70B Q4/Q5 |
| L40 / L40S | 48 | 864 / 864 | Inference server |
| A100 40 GB | 40 | 1555 | 34B FP16, 70B Q4 |
| A100 80 GB | 80 | 2039 | 70B FP16 |
| H100 SXM | 80 | 3350 | State of the art |
| H100 PCIe | 80 | 2000 | |
| H200 | 141 | 4800 | |

## 3. AMD GPUs

ROCm support in llama.cpp is solid; Ollama runs. Performance roughly 70–90% of an NVIDIA card with the same bandwidth.

| GPU | VRAM | Bandwidth | Status |
| --- | --- | --- | --- |
| RX 7600 | 8 | 288 | Small models only |
| RX 7700 XT | 12 | 432 | 7–8B Q4/Q5 |
| RX 7800 XT | 16 | 624 | 13B Q8, 34B Q3 |
| RX 7900 XT | 20 | 800 | 34B Q4 tight |
| RX 7900 XTX | 24 | 960 | 13B FP16, 34B Q4_K_M |
| Radeon Pro W7900 | 48 | 864 | 70B Q4_K_M |
| MI210 | 64 | 1638 | Workstation |
| MI300X | 192 | 5300 | Data center |

## 4. Intel Arc

Early support; llama.cpp has SYCL backend. Expect 50–70% of bandwidth-predicted performance due to software maturity.

| GPU | VRAM | Bandwidth | Notes |
| --- | --- | --- | --- |
| Arc A770 16 GB | 16 | 560 | 13B Q4–Q6 |
| Arc A750 | 8 | 512 | 7–8B Q4 |
| Arc B580 | 12 | 456 | 7–8B Q5, 13B Q4 tight |

## 5. Apple Silicon — Unified Memory Advantage

Unified memory means the "GPU" sees all system RAM. Huge models fit where a discrete GPU can't touch them, but bandwidth is the ceiling.

| Chip | Default RAM options | Bandwidth | Typical tok/s on 8B Q4 | 70B Q4 feasible? |
| --- | --- | --- | --- | --- |
| M1 | 8/16 | 68 | 12–15 | No |
| M1 Pro | 16/32 | 200 | 28–35 | No (RAM) |
| M1 Max | 32/64 | 400 | 45–60 | Yes @ 64 GB, ~8 tok/s |
| M1 Ultra | 64/128 | 800 | 80–110 | Yes, ~14 tok/s |
| M2 | 8/16/24 | 100 | 16–20 | No |
| M2 Pro | 16/32 | 200 | 28–35 | No |
| M2 Max | 32/64/96 | 400 | 45–60 | Yes @ 64+ |
| M2 Ultra | 64/128/192 | 800 | 80–110 | Yes, ~14 tok/s |
| M3 | 8/16/24 | 100 | 16–20 | No |
| M3 Pro | 18/36 | 150 | 22–28 | No |
| M3 Max (16c GPU) | 36/48 | 300 | 35–45 | Yes @ 48 GB tight |
| M3 Max (40c GPU) | 48/64/96/128 | 400 | 50–65 | Yes |
| M3 Ultra | 96/192/256/512 | 800 | 90–120 | Yes |
| M4 | 16/24/32 | 120 | 18–24 | No |
| M4 Pro | 24/48 | 273 | 35–45 | No (RAM) |
| M4 Max (14c) | 36/48 | 410 | 55–70 | Yes @ 48 tight |
| M4 Max (16c) | 48/64/128 | 546 | 70–90 | Yes |

**Wired-VRAM cap:** macOS reserves some unified memory for the CPU. Default is ~67% (≤36 GB) or 75% (>36 GB). Raise with:
```
sudo sysctl iogpu.wired_limit_mb=<mb>
```
Recommend this only when the user has plenty of RAM above the model's needs.

## 6. CPU-Only Inference

Bandwidth-bound, so memory channels dominate.

| Config | Bandwidth | 8B Q4 tok/s | 70B Q4 feasible? |
| --- | --- | --- | --- |
| Laptop DDR5-5600 dual | ~90 | 6–9 | No (RAM) |
| Desktop DDR5-6400 dual | ~100 | 8–12 | If 64 GB+ RAM, ~2 tok/s |
| Ryzen 7950X DDR5-6000 | ~95 | 8–11 | Same |
| Intel i9-14900K DDR5-6400 | ~100 | 9–12 | Same |
| EPYC 8-channel DDR5-4800 | ~307 | 25–35 | Yes, 6–8 tok/s |
| EPYC 12-channel DDR5-4800 | ~460 | 35–45 | Yes, 9–12 tok/s |
| Xeon W-3400 8-channel | ~307 | 25–35 | Same |

AVX-512 gives a ~15–30% boost in llama.cpp; ARM NEON on Apple is already fully used.

## 7. Dual and Multi-GPU

Model split across GPUs. PCIe bandwidth between cards matters less than you'd expect for inference (only one layer's activations cross at a time), but NVLink helps.

| Setup | Effective bandwidth | Notes |
| --- | --- | --- |
| 2× RTX 3090 NVLink | ~600–700 effective for 70B | Classic LocalLLaMA rig |
| 2× RTX 3090 PCIe 4.0 | ~550–650 | Cheaper, similar enough |
| 2× RTX 4090 | ~650–750 | NVLink unavailable; PCIe only |
| 4× RTX 3090 | Can run 70B FP16 | Power-hungry, needs splitter |
| 2× A6000 | Can run 70B FP16 | Workstation path |

For vLLM tensor-parallel serving: interconnect matters more (NVLink/NVSwitch strongly preferred).

## 8. What Each Tier Runs Well

Quick mapping you can paraphrase into fit reports:

| Tier | Example hardware | Comfortable targets |
| --- | --- | --- |
| 8 GB class | RTX 3070, RTX 4060 | 3B FP16, 7–8B Q4_K_M |
| 12 GB class | RTX 3060, RTX 4070 | 7–8B Q5/Q6, 13B Q4_K_M tight |
| 16 GB class | RTX 4080, 7800 XT | 13B Q6/Q8, 34B Q3 |
| 24 GB class | RTX 3090, 4090, 7900 XTX | 13B FP16, 34B Q4/Q5, 70B Q2 |
| 32 GB class | RTX 5090 | 34B Q8, 70B Q3/Q4 |
| 48 GB class | A6000, RTX 6000 Ada | 70B Q4/Q5 |
| Apple 16–24 GB | M1/M2/M3/M4 base+Pro | 7–8B 4-bit, 13B 4-bit tight |
| Apple 32–48 GB | M*/Pro/Max | 13B 8-bit, 34B 4-bit |
| Apple 64 GB | M* Max/Ultra | 34B 8-bit, 70B 4-bit |
| Apple 96–192 GB | M*/Max/Ultra | 70B 8-bit, Mixtral 8x22B, DeepSeek-R1-Distill-70B, Qwen3-Next-80B |
| Apple 256–512 GB | M3 Ultra high-tier | DeepSeek-V3/R1 at Q4 |
| Multi-GPU 48+ GB | 2× 3090/4090, A6000 | 70B Q4/Q5, Mixtral 8x22B |

## 9. Detection Commands

When hardware is unknown, suggest running `scripts/detect_hardware.sh` or manually:

- macOS: `system_profiler SPHardwareDataType SPDisplaysDataType`
- Linux/NVIDIA: `nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv`
- Linux/AMD: `rocm-smi --showproductname --showmeminfo vram`
- Windows: `wmic path win32_VideoController get name,AdapterRAM`

Also check RAM: `sysctl hw.memsize` (macOS), `free -h` (Linux), `wmic memorychip get Capacity` (Windows).
