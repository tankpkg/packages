# Decision Workflow — From User Message to Fit Report

Sources: Synthesis of this skill's other references (search-protocol, memory-math, throughput-estimation, hardware-profiles, inference-engines), plus real consultation flows from r/LocalLLaMA and HF community discussions.

Covers: the end-to-end procedure, three worked examples, common failure modes, and what to ask when information is missing.

## 1. End-to-End Procedure

```
Step 1 — Capture
  - Record the user's model name verbatim. Do not normalize.
  - Record hardware. If absent, offer scripts/detect_hardware.sh or ask.
  - Record desired context length and use case (chat / coding / agent / batch).

Step 2 — Resolve the model
  - Apply references/search-protocol.md.
  - Collect: params (B), architecture (dense/MoE), native precision,
    context window, tokenizer, layer count, KV heads, head_dim if possible.
  - Save the URL you used as the source of truth.

Step 3 — Identify candidate quants
  - Match quant format to engine/hardware (references/inference-engines.md §3).
  - List 3–4 quants from largest to smallest that are worth considering.

Step 4 — Compute fit for each candidate
  - weights_gb   = params_B × bytes_per_param (references/memory-math.md §2)
  - kv_gb        = formula from references/memory-math.md §3 (or per-token table)
  - overhead_gb  = 0.5 to 2 GB depending on engine
  - total_gb     = weights + kv + overhead
  - Compare to available memory using the safe-target percentages (§5 of memory-math).

Step 5 — Estimate throughput
  - Apply references/throughput-estimation.md formula.
  - tps = effective_bandwidth / active_weight_bytes_per_token
  - Multiply by engine efficiency (0.7–0.95).
  - Apply thermal drop if laptop or passive cooling.

Step 6 — Pick engine
  - Use references/inference-engines.md §1 decision table.
  - Name a specific CLI or API path.

Step 7 — Apply the verdict rubric
  - ✅ Runs well: total ≤ 85% memory AND tps ≥ 15
  - ⚠️ Runs but tight: total ≤ 95% AND tps 6–15
  - ❌ Won't run well: total > 95% OR tps < 5

Step 8 — Emit the Fit Report (template in SKILL.md).
```

## 2. Worked Example A — Llama-3.1-70B on RTX 4090

User: "Can I run Llama-3.1-70B on my 4090?"

**Step 1 — Capture**
- Model: `Llama-3.1-70B` (will clarify Instruct vs base during resolution).
- Hardware: RTX 4090 (24 GB VRAM, 1008 GB/s peak).
- Context: assume 8k if unspecified; ask for actual need.

**Step 2 — Resolve**
- HF: `meta-llama/Meta-Llama-3.1-70B-Instruct`. 70B dense, BF16 native, 128k context, GQA (8 KV heads), 80 layers, head_dim 128.

**Step 3 — Candidate quants**
- Q4_K_M, Q3_K_M, IQ3_XXS, IQ2_XXS, IQ2_XS.

**Step 4 — Fit**
- Q4_K_M: 70 × 0.61 = 42.7 GB → no.
- Q3_K_M: 70 × 0.49 = 34.3 GB → no.
- IQ3_XXS: 70 × 0.38 = 26.6 GB → no.
- IQ2_XS: 70 × 0.29 = 20.3 GB → maybe.
- IQ2_XXS: 70 × 0.26 = 18.2 GB + KV (320 KB × 8192 / 1024² = 2.5 GB FP16, 1.25 GB @ Q8 KV) + 0.8 GB = 20.25 GB → fits ~84% of 24 GB. ✅ barely.

**Step 5 — Throughput**
- Active weights IQ2_XXS = 18.2 GB.
- 800 / 18.2 ≈ 44 peak ceiling.
- llama.cpp efficiency 0.8 → ~35 tok/s.
- Realistic observed on this config: 25–35 tok/s.

**Step 6 — Engine**
- Ollama with custom Modelfile pointing at bartowski's IQ2_XXS GGUF, or llama.cpp directly. ExLlamaV2 2.4bpw also fits.

**Step 7 — Verdict**
- ⚠️ Runs but tight. Quality meaningfully degraded at IQ2_XXS. Recommend adding a second GPU, or renting an A6000 for serious use. For casual chat, runs usable.

**Step 8 — Report** (see template in SKILL.md).

## 3. Worked Example B — Qwen2.5-14B on M2 Pro 16 GB

User: "Will Qwen2.5-14B run OK on my M2 Pro MacBook (16 GB)?"

**Resolve:** `Qwen/Qwen2.5-14B-Instruct`, 14B dense, BF16, 32k context, 48 layers, 8 KV heads, head_dim 128.

**Candidate quants (MLX):** 4-bit and 3-bit.

**Fit at 8k context:**
- 4-bit weights: 14 × 0.50 = 7.0 GB.
- KV per token (FP16): 192 KB. 8k → 1.5 GB.
- Overhead: 0.5 GB.
- Total: 9.0 GB. Budget at 70%: 16 × 0.7 = 11.2 GB.
- ✅ fits comfortably at 4-bit, 8k.

**Throughput:**
- Effective bandwidth 160 GB/s. Weight size 7.0 GB.
- 160 / 7.0 ≈ 23 tok/s.
- MLX efficiency 0.85 → ~20 tok/s. Sustained on battery ~15.

**Engine:** MLX (`mlx-community/Qwen2.5-14B-Instruct-4bit`). Alternative: Ollama GGUF (`qwen2.5:14b-instruct-q4_K_M`), ~10–15% slower on M-series.

**Verdict:** ✅ Runs well for interactive chat. For coding assistants, sustained throughput on battery may feel slow; plug in.

## 4. Worked Example C — Qwen3-Next-80B-A3B on a hypothetical box

User: "Can I run Qwen3-Next-80B on my M4 Max 128 GB?"

**Step 2 — Resolve.** Assume the agent has not seen this model in training. It still searches:
- HF: `Qwen/Qwen3-Next-80B-A3B-Instruct`.
- Params: 80B total, 3B active per token. MoE.
- Native FP16/BF16, context long (confirm from card).

**Fit at 8k context, MLX 4-bit:**
- Weights total 80 × 0.50 = 40.0 GB (all experts resident).
- KV: depends on architecture; use conservative 128 KB/token (MoE, GQA).
  8k → 1.0 GB.
- Overhead: 0.6 GB.
- Total: 41.6 GB. Budget: 128 × 0.70 = 89.6 GB. ✅ comfortable.

**Throughput (MoE):**
- Active 3B × 0.50 = 1.5 GB per token.
- 440 / 1.5 ≈ 293 ceiling.
- MoE routing overhead → realistic 100–150 tok/s.
- Worth stating as "very fast for an 80B-class model thanks to the MoE active-param count."

**Engine:** MLX if an `mlx-community` quant exists; otherwise Ollama with a community GGUF (still fast on unified memory).

**Verdict:** ✅ Runs well, genuinely fast.

## 5. Common Failure Modes

### "I think you mean Qwen2.5" (Substitution)

Caught by `references/search-protocol.md` §1. Never answer a different model than the one asked about. If you truly cannot resolve after exhaustive search, ask for a link.

### "70B will run fine on my 3090"

Without math it sounds plausible; it isn't. 70B dense even at Q4_K_M is 42 GB. Always do the weights + KV + overhead sum before claiming fit.

### "Just run FP16"

On consumer GPUs, FP16 of any model above ~13B won't fit in 24 GB. Default to Q5_K_M or Q4_K_M unless the user has the VRAM for FP16.

### "MoE is fast because it's bigger"

MoE is fast because active params are small, but total params still occupy memory. A 671B MoE won't fit on a 24 GB GPU no matter how low the active count is.

### "Bandwidth estimates are exact"

They are ceilings with 70–90% real-world efficiency. State them as ranges ("~25–35 tok/s"), not single numbers.

### "Partial offload will be fine"

It rarely is. If less than 60% of layers fit on GPU, throughput collapses to near CPU-only. Prefer a smaller quant that fully fits.

### "Laptop GPU = desktop GPU with the same name"

It doesn't. Laptop 4090 is 16 GB with ~576 GB/s, not 24 GB/1008 GB/s. Always clarify.

### "Apple unified memory magically runs anything"

Only up to the wired-VRAM cap (~67–75% of RAM), and only at the bandwidth of the chip. A base M3 at 100 GB/s is not going to run 70B at useful speeds.

## 6. When You're Missing Info — Ask, Don't Guess

| Missing | Ask |
| --- | --- |
| Hardware | "What GPU/CPU and how much VRAM/RAM? Or run this command: `...`" |
| Use case | "Interactive chat, coding assistant, batch processing, or agent loops?" |
| Context length | "How long are your typical prompts + expected replies? (KV cache scales with this.)" |
| Acceptable quality | "Are you OK with Q4 quantization, or do you need near-FP16 quality?" |
| Engine preference | "Ollama (easy), MLX (Mac speed), ExLlamaV2 (NVIDIA speed), vLLM (serving)?" |
| Model ambiguity | "There are multiple `Llama-4` variants; which exactly? (paste the HF repo URL if unsure)" |

Ask once, concisely. Prefer producing the report with reasonable defaults over long interviews.

## 7. Pre-Emit Checklist

Before sending the Fit Report:

- [ ] Model name in the report matches the user's exact string.
- [ ] I cited a resolution URL (HF/Ollama/vendor).
- [ ] Memory math shows weights + KV + overhead with numbers.
- [ ] Throughput is a range with engine and sustained-vs-peak noted if relevant.
- [ ] Engine pick has a reason.
- [ ] Verdict matches the rubric.
- [ ] No substitution happened silently.

If any box is unchecked, fix before sending.
