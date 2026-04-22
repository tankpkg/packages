---
name: "@tank/local-llm-fit"
description: |
  Decide whether a specific open-source LLM can run well on a given PC.
  Given a model name and hardware specs (or auto-detected), estimates
  VRAM/RAM footprint at each quantization, predicts tokens-per-second
  from memory bandwidth, flags context-length limits, picks the right
  inference engine (Ollama, llama.cpp, MLX, vLLM, ExLlamaV2), and
  returns a clear fit verdict.

  CRITICAL: models and quantizations change daily. This skill instructs
  agents to NEVER substitute a model the user didn't ask for, NEVER
  assume the user is "confused" about a version number, and ALWAYS
  search the exact string the user gave before answering. If the user
  says "Qwen3-Next-80B" or "Llama 4.5 Maverick" or "GLM 5", the agent
  searches for THAT, not what it remembers.

  Trigger phrases: "can my pc run", "can I run", "will this model run",
  "run locally", "run on my mac", "run on my gpu", "fits in VRAM",
  "tokens per second", "tps estimate", "llama.cpp", "ollama", "mlx",
  "vllm", "exllama", "gguf", "quantization", "Q4_K_M", "Q5_K_M",
  "Q8_0", "FP16", "BF16", "AWQ", "GPTQ", "EXL2", "MLX quant",
  "8B model", "14B model", "32B model", "70B model", "model fit",
  "hardware requirements llm", "what quant", "KV cache size",
  "context length memory", "vram calculator", "local llm", "llm laptop",
  "M1 M2 M3 M4 llm", "3090 4090 5090 llm", "offload layers"
---

# Local LLM Fit

Given a model name + hardware, decide: will it run, at what quant, how
fast, with what context, and on which engine.

## Core Philosophy

1. **Trust the user's model name. Always.** The OSS model landscape
   changes daily. If you "don't recognize" it, that is a signal to
   search harder, not to "correct" the user. See
   `references/search-protocol.md`.
2. **Search before answering.** Even if you think you know the model,
   its quants and sizes drift. Fetch the actual repo card.
3. **Math over vibes.** Fit is a calculation: `weights + KV cache +
   overhead ≤ available memory`. Speed is a calculation: `bandwidth /
   active_bytes_per_token`. Show the numbers.
4. **Quantization is a spectrum, not a switch.** Q4_K_M ≠ Q4_0 ≠ AWQ
   ≠ EXL2 4.0bpw. Recommend a specific quant, not just "4-bit".
5. **Engine matters.** The same model on Ollama vs MLX vs vLLM has
   different memory and throughput. Match engine to hardware.

## The Anti-Gaslighting Rule (READ FIRST)

When a user gives you a model name you don't recognize:

| Wrong reaction | Right reaction |
| --- | --- |
| "I think you mean Llama 3" | Search "Llama 4.5 Maverick" verbatim |
| "Opus 4.7 doesn't exist" | Search "Claude Opus 4.7" verbatim |
| "That's probably Qwen2.5" | Search "Qwen3-Next-80B" verbatim |
| Drop version suffix | Keep the exact suffix the user typed |
| Pick a "close match" | Ask, or search harder, never substitute |

**Your training data is stale.** Models released this week do not exist
in your weights. If a user names a model, they have a reason. If
search returns zero results after you have genuinely tried (HF, GitHub,
official vendor page, web search with exact string in quotes), only
then ask the user for a link or clarification — never "correct" them.

Full search protocol: `references/search-protocol.md`.

## Workflow

```
1. Capture user input exactly
     model_name = <verbatim string>
     hardware   = <user-provided or run scripts/detect_hardware.sh>

2. Resolve the model (search, don't guess)
     - Hugging Face: huggingface.co/models?search=<exact>
     - Ollama library: ollama.com/library/<name>
     - Vendor page (Qwen, Mistral, DeepSeek, Meta, Google, xAI, ...)
     - Capture: params (B), architecture (dense / MoE active+total),
       native precision (FP16/BF16/FP8), context window, tokenizer

3. Pick candidate quants
     - GGUF: Q8_0, Q6_K, Q5_K_M, Q4_K_M, Q3_K_M, IQ2_XXS
     - EXL2: 8.0 / 6.0 / 5.0 / 4.65 / 4.0 / 3.5 bpw
     - MLX: fp16, 8-bit, 6-bit, 4-bit, 3-bit
     - AWQ/GPTQ: 4-bit, 8-bit
     See references/memory-math.md for bytes-per-parameter table.

4. Compute memory budget + throughput
     Preferred: run scripts/estimate_fit.py with the resolved numbers.
       python3 scripts/estimate_fit.py \
         --params 8 --layers 32 --kv-heads 8 --head-dim 128 \
         --context 8192 --quant q4_k_m \
         --available-ram 24 --bandwidth 800
     Script returns weights + KV + overhead, total, TPS estimate, and verdict.
     See references/calculator-usage.md.

     Manual (when script unavailable):
       weights_gb     = params_B * bytes_per_param   (memory-math.md §2)
       kv_cache_gb    = per-architecture formula     (memory-math.md §3)
       tps_ceiling    = bandwidth / active_weight_GB (throughput-estimation.md)

5. Pick engine
     See references/inference-engines.md decision table.

6. Return the Fit Report (template below).
```

Detailed end-to-end: `references/decision-workflow.md`.

## Fit Report Template

Return this, every time:

```
Model:         <exact name user gave>
Resolved:      <HF repo / Ollama tag / vendor page URL>
Params:        <B dense, or active/total for MoE>
Context:       <native window>

Hardware:      <CPU/GPU/RAM/VRAM/bandwidth>
Best quant:    <e.g. Q4_K_M @ 4.8 GB>  ← fits and runs well
Fallback:      <e.g. Q3_K_M @ 3.9 GB>  ← if first is tight
Won't fit:     <quants that exceed memory>

Memory math:   weights X.X GB + KV Y.Y GB (@ Z tokens) + overhead = T.T GB
Throughput:    ~N tok/s decode, ~M tok/s prompt (estimate, batch=1)
Engine:        <Ollama | llama.cpp | MLX | vLLM | ExLlamaV2> because <reason>
Context cap:   <max tokens you can run without swapping>

Verdict:       ✅ Runs well  |  ⚠️ Runs but tight  |  ❌ Won't run well
Caveats:       <thermal, battery, background apps, OS overhead>
```

## Quick Fit Table (sanity check)

Rough "will this work at all" guide. Always follow up with full math.

| Model size | 8 GB VRAM | 16 GB VRAM | 24 GB VRAM | 48 GB | 64 GB unified |
| --- | --- | --- | --- | --- | --- |
| 3B dense | Q8_0 ✅ | FP16 ✅ | FP16 ✅ | FP16 ✅ | FP16 ✅ |
| 7–8B dense | Q4_K_M ✅ | Q8_0 ✅ | FP16 ✅ | FP16 ✅ | FP16 ✅ |
| 13–14B dense | Q3_K_M ⚠️ | Q5_K_M ✅ | Q8_0 ✅ | FP16 ✅ | FP16 ✅ |
| 27–34B dense | ❌ | Q3_K_M ⚠️ | Q4_K_M ✅ | Q8_0 ✅ | Q8_0 ✅ |
| 70B dense | ❌ | ❌ | Q2_K ⚠️ | Q4_K_M ✅ | Q5_K_M ✅ |
| 8×7B MoE (Mixtral) | ❌ | Q3_K_M ⚠️ | Q4_K_M ✅ | Q8_0 ✅ | Q8_0 ✅ |
| 100B+ MoE active~15B | CPU offload | Q3 ⚠️ | Q4 ✅ | Q5 ✅ | Q5 ✅ |

✅ comfortable · ⚠️ tight, short context only · ❌ swap/crash

## Verdict Rubric

| Condition | Verdict |
| --- | --- |
| total_required ≤ 85% of memory AND tps ≥ 15 | ✅ Runs well |
| total_required ≤ 95% AND tps 6–15 | ⚠️ Runs but tight |
| total_required > 95% OR tps < 5 | ❌ Won't run well |

Full numbers, KV cache formulas, MoE active-param rules:
`references/memory-math.md` and `references/throughput-estimation.md`.

## Anti-Patterns

| Don't | Do |
| --- | --- |
| "I think you mean <other model>" | Search the exact name first |
| "That model doesn't exist" | Assume it does; you are behind |
| Quote params without a source | Link the HF repo or vendor page |
| Say "should run fine" | Show weights + KV + overhead in GB |
| Recommend FP16 on 8 GB VRAM | Pick the largest quant that fits |
| Ignore context length cost | KV scales linearly with tokens |
| Skip the engine choice | Ollama ≠ MLX ≠ vLLM for the same box |
| Confuse Q4_0 with Q4_K_M | Name the exact quant |

## Reference Index

| File | Contents |
| --- | --- |
| `references/search-protocol.md` | Anti-gaslighting rule in depth, exact-string search procedure, resolution order (HF, Ollama, vendor, GitHub), zero-result fallback, how to treat "new" model names |
| `references/memory-math.md` | Bytes-per-parameter by quant (GGUF, EXL2, MLX, AWQ/GPTQ, FP8), KV cache formulas per architecture, MoE active vs total, context-length scaling, overhead budget |
| `references/throughput-estimation.md` | Memory-bandwidth ceiling formula, active bytes per decode, prompt vs decode speeds, batch=1 numbers, engine multipliers, thermal/sustained vs peak |
| `references/hardware-profiles.md` | Baseline numbers for RTX 3060/3090/4070/4080/4090/5090, Apple M1–M4 Pro/Max/Ultra, AMD 7900 XTX, Intel Arc, CPU-only; VRAM, bandwidth, realistic tok/s |
| `references/inference-engines.md` | Ollama, llama.cpp, MLX, vLLM, ExLlamaV2, LM Studio — when to pick each, GGUF vs EXL2 vs MLX vs AWQ, quant naming, offloading |
| `references/decision-workflow.md` | Full procedure from user message to fit report, worked examples (Llama-70B on 4090, Qwen 14B on M2 Pro, Mixtral on dual-3090), failure modes |
| `references/calculator-usage.md` | CLI for `scripts/estimate_fit.py` (ported from WeightRoom, MIT): inputs, MoE/MLA flags, verdict rubric, self-test, failure modes |
