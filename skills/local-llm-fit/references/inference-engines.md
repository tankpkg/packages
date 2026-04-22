# Inference Engines — Picking the Right Runtime

Sources: llama.cpp repo + docs, Ollama docs, Apple MLX docs, vLLM docs, ExLlamaV2 (turboderp) repo, LM Studio release notes, MLC LLM, community benchmarks (2023–2026).

Covers: which engine to pick per hardware, quant format compatibility, what each engine is good at, and the traps in offloading and configuration.

## 1. The Decision Table

Match user's hardware to engine. In order of recommendation.

| Hardware | Primary | Alternative | Avoid |
| --- | --- | --- | --- |
| Apple Silicon, small models | MLX | Ollama | Transformers+bnb |
| Apple Silicon, max throughput | MLX | llama.cpp (Metal) | vLLM |
| NVIDIA, single GPU, want simple | Ollama | llama.cpp | vLLM |
| NVIDIA, single GPU, max single-stream | ExLlamaV2 | llama.cpp (CUDA) | Transformers |
| NVIDIA, multi-GPU serving | vLLM | TensorRT-LLM | Ollama |
| AMD ROCm | llama.cpp | Ollama (ROCm) | vLLM (partial) |
| Intel Arc | llama.cpp SYCL | IPEX-LLM | ExLlamaV2 |
| CPU-only | llama.cpp | Ollama | vLLM |
| Windows, GUI-focused | LM Studio | Ollama | — |
| Mixed hardware, switching models | Ollama | LM Studio | — |

## 2. Engine Profiles

### Ollama

- Wraps llama.cpp with a CLI and a REST API. Zero-config for most people.
- Handles model pulls, quant selection, system prompts, KV cache config.
- Supports CUDA, Metal, ROCm.
- Library at `ollama.com/library/<name>` with curated tags like `llama3.1:8b`, `qwen2.5:14b-instruct-q5_K_M`.
- Memory efficiency: same as llama.cpp.
- Weakness: harder to use bleeding-edge models before they're added to the library. Workaround: `ollama create` with a custom Modelfile pointing at a local GGUF.

### llama.cpp

- The reference CPU/GPU inference engine for GGUF.
- CUDA, Metal, ROCm, SYCL (Intel), Vulkan backends.
- Fine-grained control: `-ngl` (layers offloaded to GPU), `-c` (context), `-ctk/-ctv` (KV cache quant), `-fa` (flash attention), `--rope-freq-*` (context scaling).
- Quant formats: Q8_0, Q6_K, Q5_K_M, Q5_K_S, Q4_K_M, Q4_K_S, Q3_K_M, Q3_K_S, Q2_K, IQ* (imatrix) variants.
- Use when: you need partial GPU offload, want to tune context/KV, or are running on non-NVIDIA hardware.
- Key flags to mention in reports:
  - `-ngl 999` → put all layers on GPU (or fewer for partial offload).
  - `-c 8192` → context window.
  - `-ctk q8_0 -ctv q8_0` → KV cache at 8-bit; halves KV memory.
  - `-fa` → Flash Attention; ~5–10% faster on CUDA/Metal.

### Apple MLX

- Native Apple Silicon framework. Uses Metal and AMX.
- Best tok/s and best memory efficiency on Apple hardware.
- Quants: fp16, 8-bit, 6-bit, 4-bit, 3-bit (new). Community repos on `mlx-community`.
- Supports long context better than llama.cpp Metal for some models.
- Use when: user is on M-series Mac.
- CLI: `mlx_lm.generate --model mlx-community/Qwen2.5-14B-Instruct-4bit --prompt "..."`.
- Server: `mlx_lm.server` exposes an OpenAI-compatible endpoint.

### ExLlamaV2 (turboderp)

- Single-GPU NVIDIA speed champion for EXL2 and GPTQ quants.
- Uses tensor cores efficiently; fastest batch=1 decode.
- Variable-bit EXL2 lets you fine-tune fit: pick 4.65bpw for a 24 GB card targeting 70B.
- No CPU offload. If it doesn't fit in VRAM, it doesn't run.
- Use when: user has NVIDIA, wants max tok/s, and is OK with a Python/text-gen-webui setup.

### vLLM

- Production serving engine: paged KV, continuous batching, tensor parallel, OpenAI-compatible API.
- Best for serving many concurrent requests.
- Heavier overhead at batch=1 than ExLlamaV2 or llama.cpp (1–2 GB, CUDA graphs).
- Supports AWQ, GPTQ, FP8, and more via HF checkpoints.
- Use when: user is serving, not chatting solo. Multi-GPU tensor parallelism shines here.

### LM Studio

- GUI wrapper around llama.cpp / MLX with a model browser.
- Great for non-technical users. Ships with a built-in OpenAI-compatible server.
- Memory and speed identical to llama.cpp/MLX.

### TensorRT-LLM

- NVIDIA's enterprise engine. Highest throughput, most complex setup.
- Use when: user mentions NIM, Triton, or production H100/H200 deployment.

### MLC LLM

- Cross-platform (incl. mobile, web, ROCm, Metal) via TVM compilation.
- Useful when user targets WebGPU or Android/iOS.

### Transformers + bitsandbytes

- Huggingface's default path. Works everywhere but slow.
- Use only when no community quant exists yet and you need to try a brand-new model immediately.

## 3. Quant Format Compatibility Matrix

| Quant | llama.cpp/Ollama | MLX | ExLlamaV2 | vLLM | Transformers |
| --- | --- | --- | --- | --- | --- |
| GGUF (Q*_K_M etc.) | ✅ native | ❌ | ❌ | partial | ❌ |
| EXL2 | ❌ | ❌ | ✅ native | ❌ | ❌ |
| AWQ | ❌ | ❌ | ✅ | ✅ | ✅ |
| GPTQ | ❌ | ❌ | ✅ | ✅ | ✅ |
| MLX 4-bit / 8-bit | ❌ | ✅ native | ❌ | ❌ | ❌ |
| FP8 (NVIDIA) | ❌ | ❌ | ❌ | ✅ (H100/Ada) | partial |
| bnb nf4 / int8 | ❌ | ❌ | ❌ | ❌ | ✅ |

Practical consequences:
- If the user's hardware is Apple: point them at MLX quants, not GGUF.
- If NVIDIA GPU-only, max speed: ExLlamaV2 with EXL2 or GPTQ.
- If NVIDIA GPU-only, convenience: Ollama/llama.cpp with GGUF.
- If serving multiple users: vLLM with AWQ.

## 4. Offloading — Where People Lose Speed

Partial GPU offload runs some layers on GPU, the rest on CPU. Huge speed penalty but fits models that otherwise won't.

With llama.cpp / Ollama:
- `-ngl N` in llama.cpp, `OLLAMA_NUM_GPU` env or Modelfile `PARAMETER num_gpu` in Ollama.
- N = number of layers sent to GPU. Start with total layers, reduce until it fits.
- Offloaded layers go through PCIe every token → big speed drop.

Rule of thumb: if fewer than ~60% of layers fit on GPU, throughput falls toward CPU-only speeds. When recommending a fit, prefer "fits entirely in VRAM at a smaller quant" over "partial offload at a larger quant."

Exception: Apple's unified memory means there is no CPU↔GPU copy — "offloading" is irrelevant there.

## 5. Context Length Config Pitfalls

- Ollama: default context is often 2048 or 4096. For long-context models, set `PARAMETER num_ctx 32768` in the Modelfile or pass `options: { num_ctx: 32768 }` over the API.
- llama.cpp: `-c 32768`, and ensure `-fa` is on for GQA models.
- MLX: context handled automatically but RAM rises linearly; monitor.
- Never claim "200k context works" without checking the model's own rope scaling and the engine's implementation status.

## 6. Flash Attention and KV Quantization

- Flash Attention v2/v3 reduces activations memory and speeds up prompt. Always on where supported.
- KV cache quant (q8_0 / q4_1) halves/quarters KV size. q8_0 is near-lossless; q4 noticeably degrades long-context retrieval for some models. Recommend q8_0 KV when context is the bottleneck.

## 7. Mapping User Intent to Engine

| User says | Likely best engine |
| --- | --- |
| "just want to try it" | Ollama |
| "on my Mac" | MLX (large) or Ollama (convenience) |
| "max tokens per second on my 3090/4090" | ExLlamaV2 (EXL2/GPTQ) |
| "serving to my team" | vLLM |
| "don't want CLI" | LM Studio |
| "on my AMD / Intel card" | llama.cpp (ROCm/SYCL) |
| "use it in my app via API" | Ollama or MLX server (local); vLLM (prod) |
| "phone / browser" | MLC LLM |

## 8. Report-Ready Sentence

Be specific about engine and reason:

> "On your RTX 4090, run Qwen2.5-32B at Q4_K_M via Ollama (pulls `qwen2.5:32b-instruct-q4_K_M`, ~19.5 GB weights + ~2 GB KV at 8k context + ~0.8 GB overhead = 22.3 GB). Expect ~40 tok/s decode, ~600 tok/s prompt. For ~10% more speed, switch to ExLlamaV2 with a 4.65bpw EXL2 quant from turboderp or bartowski."
