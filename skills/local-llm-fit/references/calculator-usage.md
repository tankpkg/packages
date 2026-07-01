# Calculator Usage — scripts/estimate_fit.py

Sources: Port of smelukov/WeightRoom (MIT), community-measured GGUF/MLX/EXL2 bits-per-param tables, @tank/local-llm-fit reference docs.

Covers: when to use the script, how to call it, input fields, output interpretation, all supported quants, MoE and MLA handling, and failure modes.

## When To Use The Script

Use the calculator when you have the model resolved and the hardware known. Do not use it to guess model specs — that violates the core rule in `search-protocol.md`. The flow is:

```
1. Agent receives "can I run <model> on <hardware>?"
2. Agent resolves <model> via search-protocol.md. Gets:
     params, layers, kv_heads, head_dim, context, precision,
     [MoE: active_params], [DeepSeek: kv_lora_rank, qk_rope_head_dim]
3. Agent resolves <hardware>. Gets:
     available_ram_gb, bandwidth_gb_per_s
4. Agent calls scripts/estimate_fit.py with the numbers.
5. Agent formats the Fit Report using the script's output.
```

The script is deterministic. Two agents with the same inputs produce the same numbers. The report template in `SKILL.md` is still the authoritative output format — the script populates the numeric fields.

## Minimal Invocation

```bash
python3 scripts/estimate_fit.py \
  --params 8 --layers 32 --kv-heads 8 --head-dim 128 \
  --context 8192 --quant q4_k_m \
  --available-ram 24 --bandwidth 800
```

Output:
```
Model params:      8.0 B
Quant:             q4_k_m (KV: fp16)
Context:           8,192 tokens
Architecture:      layers=32 kv_heads=8 head_dim=128 formula=standard

Weights:           5.3 GB
KV cache:          1.1 GB
Overhead:          1.0 GB
Total required:    7.4 GB
Available memory:  24.0 GB  (31% used — fits)
Throughput:        ~100.0 tok/s decode (ceiling ~120.2, batch=1)

Verdict:           ✅ runs well
```

## Required Inputs

| Flag | Source in config.json | Notes |
| --- | --- | --- |
| `--params` | `num_parameters`, or sum from `safetensors.total_size / bytes_per_param` | In billions. For MoE, this is total. |
| `--layers` | `num_hidden_layers` | |
| `--kv-heads` | `num_key_value_heads` | GQA. For MHA, equals `num_attention_heads`. |
| `--head-dim` | `hidden_size / num_attention_heads` | |

If any of these are missing from the model card, go back to `search-protocol.md §10` and find them. Do not guess.

## Optional Inputs

| Flag | Default | When to change |
| --- | --- | --- |
| `--context` | 8192 | User's actual prompt+reply length expectation |
| `--quant` | q4_k_m | Try larger if fits, smaller if doesn't |
| `--kv-quant` | fp16 | Set `q8` to halve KV when context is the bottleneck |
| `--available-ram` | 0 | GB of VRAM (discrete GPU) or unified RAM (Apple) |
| `--bandwidth` | 0 | GB/s from `hardware-profiles.md`. 0 = skip TPS math. |
| `--efficiency` | 0.8 | Engine efficiency. ExLlamaV2 ~0.9, vLLM batch=1 ~0.7 |
| `--overhead` | 1.0 | GB. vLLM: 1.5–2, MLX/llama.cpp: 0.5–0.8 |
| `--moe` + `--active-params` | off | Required for Mixtral, Qwen3-MoE, DeepSeek |
| `--kv-formula` | standard | `mla` for DeepSeek, `hybrid` for Gemma 2/3, `linear_hybrid` for Qwen3-Next |
| `--sliding-window` | 4096 | Gemma 2: 4096, Gemma 3: 1024 |
| `--full-layers` | layers/2 or /4 | Hybrid architectures |
| `--kv-lora-rank` | 512 | MLA only (DeepSeek V2: 512, V3: 512) |
| `--qk-rope-head-dim` | 64 | MLA only |
| `--concurrent-users` | 1 | Single-user local = 1. Serving = actual parallel slots. |
| `--kv-fill-pct` | 100 | llama.cpp pre-alloc: 100, vLLM PagedAttention typical: 25 |

## Supported Quants

Human-readable tag → internal bits per param:

| Tag | Bits | Family | Engine |
| --- | --- | --- | --- |
| `fp32` | 32 | — | all |
| `fp16`, `bf16` | 16 | — | all |
| `fp8` | 8 | — | vLLM on H100/Ada |
| `q8`, `q8_0` | 8.5 | GGUF | llama.cpp, Ollama |
| `q6_k` | 6.56 | GGUF | llama.cpp, Ollama |
| `q5_k_m`, `q5_k_s`, `q5_0` | 5.68 / 5.52 / 5.5 | GGUF | llama.cpp, Ollama |
| `q4_k_m`, `q4_k_s`, `q4_0`, `q4` | 4.84 / 4.58 / 4.55 / 4.84 | GGUF | llama.cpp, Ollama |
| `q3_k_m`, `q3_k_s` | 3.91 / 3.50 | GGUF | llama.cpp, Ollama |
| `q2_k` | 3.35 | GGUF | llama.cpp, Ollama |
| `iq3_xxs` | 3.06 | GGUF | llama.cpp |
| `iq2_xs`, `iq2_xxs` | 2.31 / 2.06 | GGUF | llama.cpp |
| `iq1_s`, `q1` | 1.56 | GGUF | llama.cpp |
| `exl2_8`, `exl2_6`, `exl2_5`, `exl2_4_65`, `exl2_4`, `exl2_3_5`, `exl2_3`, `exl2_2_4` | 8 to 2.4 | EXL2 | ExLlamaV2 |
| `mlx_8`, `mlx_6`, `mlx_4`, `mlx_3` | 8 / 6 / 4 / 3 | MLX | Apple MLX |
| `awq_4`, `awq_8` | 4 / 8 | AWQ | vLLM, ExLlamaV2 |
| `gptq_4` | 4 | GPTQ | vLLM, ExLlamaV2 |

Unknown tags fall back to q4. The script errors out loudly — prefer that over silent wrong math.

## MoE Example

Mixtral-8x7B on a dual-4090 rig (2 × 24 GB effective 48 GB, ~650 GB/s combined):

```bash
python3 scripts/estimate_fit.py \
  --params 47 --layers 32 --kv-heads 8 --head-dim 128 \
  --context 8192 --quant q4_k_m \
  --available-ram 48 --bandwidth 650 \
  --moe --active-params 13
```

The script uses 47B for memory sizing (all 8 experts resident) but 13B for throughput (2 experts active per token). Skipping `--moe`/`--active-params` on an MoE model under-predicts TPS by ~4×.

## MLA Example (DeepSeek)

DeepSeek-V3 at Q4 on a 512 GB M3 Ultra:

```bash
python3 scripts/estimate_fit.py \
  --params 37 --layers 61 --kv-heads 128 --head-dim 128 \
  --context 8192 --quant q4_k_m \
  --available-ram 512 --bandwidth 400 \
  --moe --active-params 37 \
  --kv-formula mla --kv-lora-rank 512 --qk-rope-head-dim 64
```

Note: for DeepSeek the `--params` you pass is the total active+shared path for memory math. If you want the full 671B footprint, pass that instead — the flag is a value, not a model lookup.

## Gemma 2/3 Hybrid Example

```bash
python3 scripts/estimate_fit.py \
  --params 27 --layers 46 --kv-heads 16 --head-dim 128 \
  --context 8192 --quant q4_k_m \
  --kv-formula hybrid --sliding-window 4096 --full-layers 5 \
  --available-ram 24 --bandwidth 800
```

Sliding-window layers cap at 4096 tokens of KV, so long-context Gemma is cheaper than a pure-GQA model of the same size.

## JSON Mode

For agent post-processing:
```bash
python3 scripts/estimate_fit.py ... --json
```

Returns:
```json
{
  "weights_gb": 5.3,
  "kv_cache_gb": 1.1,
  "overhead_gb": 1.0,
  "total_gb": 7.4,
  "ram_status": "fits",
  "tps_estimate": 100.0,
  "tps_ceiling": 120.2,
  "verdict": "✅ runs well",
  "notes": []
}
```

## Verdict Rubric

The script's verdict maps to SKILL.md's verdict table:

| Condition | Verdict |
| --- | --- |
| `total_gb > available_ram × 0.95` OR `tps < 5` | ❌ won't run well |
| `total_gb > available_ram × 0.85` OR `tps < 15` | ⚠️ runs but tight |
| Otherwise | ✅ runs well |

If `--available-ram` is 0, the RAM clause is skipped and verdict depends only on TPS.

## Self-Test

Before trusting the calculator on unfamiliar hardware, run:
```bash
python3 scripts/estimate_fit.py --self-test
```
Five fixtures covering dense, MoE, MLA, and tight-fit cases. All must pass.

## Failure Modes

| Symptom | Cause | Fix |
| --- | --- | --- |
| "missing required args" | Agent didn't resolve the model | Go back to `search-protocol.md §10` |
| `Unknown quant` error | Typo or exotic quant | Check the Supported Quants table |
| TPS is `None` | `--bandwidth 0` or `--params 0` | Pass bandwidth from `hardware-profiles.md` |
| "KV cache exceeds weight size" note | Long context on GQA model | `--kv-quant q8` or shorten `--context` |
| `ram_status=unknown` | `--available-ram` not passed | Pass it; verdict downgrades without it |
| TPS feels too high | Forgot engine efficiency | `--efficiency 0.7` for vLLM, `0.9` for ExLlamaV2 |

## Attribution

Formula port from smelukov/WeightRoom (MIT), with extensions for community
GGUF/MLX/EXL2 quant tags. See `scripts/NOTICE`.
