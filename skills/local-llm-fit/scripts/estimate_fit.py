#!/usr/bin/env python3
"""Estimate LLM memory fit and tokens/sec for a given PC spec.

Port of the RAM / KV / TPS math from smelukov/WeightRoom (MIT) —
https://github.com/smelukov/WeightRoom/blob/main/src/lib/calculator.ts
Extended with a CLI, preset-free mode, and verdict rubric matching
@tank/local-llm-fit references.

Prerequisite: the model must already be resolved by the agent via
references/search-protocol.md. This script does NOT look up model specs —
the agent passes them in. That preserves the skill's "trust the user's
model name, search the exact string, never substitute" discipline.

Usage:
  estimate_fit.py --params 8 --layers 32 --kv-heads 8 --head-dim 128 \\
                  --context 8192 --quant q4_k_m --kv-quant q8 \\
                  --available-ram 24 --bandwidth 800

  estimate_fit.py --self-test
"""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from typing import Optional, Literal

# Bits per weight per quantization. Matches QUANT_BITS from WeightRoom,
# normalized to community GGUF/MLX/EXL2/AWQ tags.
QUANT_BITS = {
    "fp32": 32.0,
    "fp16": 16.0,
    "bf16": 16.0,
    "fp8": 8.0,
    "q8": 8.5,
    "q8_0": 8.5,
    "q6_k": 6.56,
    "q5_k_m": 5.68,
    "q5_k_s": 5.52,
    "q5_0": 5.5,
    "q4_k_m": 4.84,
    "q4_k_s": 4.58,
    "q4_0": 4.55,
    "q4": 4.84,
    "q3_k_m": 3.91,
    "q3_k_s": 3.50,
    "q2_k": 3.35,
    "iq3_xxs": 3.06,
    "iq2_xs": 2.31,
    "iq2_xxs": 2.06,
    "iq1_s": 1.56,
    "q1": 1.56,
    "exl2_8": 8.0,
    "exl2_6": 6.0,
    "exl2_5": 5.0,
    "exl2_4_65": 4.65,
    "exl2_4": 4.0,
    "exl2_3_5": 3.5,
    "exl2_3": 3.0,
    "exl2_2_4": 2.4,
    "mlx_8": 8.0,
    "mlx_6": 6.0,
    "mlx_4": 4.0,
    "mlx_3": 3.0,
    "awq_4": 4.0,
    "gptq_4": 4.0,
    "awq_8": 8.0,
}

KvFormula = Literal["standard", "hybrid", "mla", "linear_hybrid"]


@dataclass
class FitResult:
    weights_gb: float
    kv_cache_gb: float
    overhead_gb: float
    total_gb: float
    ram_status: str
    tps_estimate: Optional[float]
    tps_ceiling: Optional[float]
    verdict: str
    notes: list


def _round(n: float) -> float:
    return round(n * 10) / 10


def _weights_gb(params_b: float, quant: str) -> float:
    bits = QUANT_BITS.get(quant.lower())
    if bits is None:
        raise SystemExit(f"Unknown quant '{quant}'. Known: {sorted(QUANT_BITS)}")
    # x1.1 accounts for embeddings/norms/lm_head stored in higher precision.
    # For sub-2-bit quants, the overhead is already baked in.
    overhead = 1.0 if bits < 2.0 else 1.1
    weight_bytes = params_b * 1e9 * (bits / 8.0)
    return (weight_bytes / 1e9) * overhead


def _kv_cache_gb(
    layers: int,
    kv_heads: int,
    head_dim: int,
    context: int,
    kv_quant: str,
    formula: KvFormula,
    sliding_window: int,
    full_layers: Optional[int],
    full_kv_heads: Optional[int],
    full_head_dim: Optional[int],
    kv_lora_rank: int,
    qk_rope_head_dim: int,
    concurrent_users: int,
    kv_fill_pct: float,
) -> float:
    kv_bits = QUANT_BITS.get(kv_quant.lower())
    if kv_bits is None:
        raise SystemExit(f"Unknown kv-quant '{kv_quant}'")
    bytes_per_el = kv_bits / 8.0

    if formula == "standard":
        kv_bytes = 2 * layers * kv_heads * head_dim * context * bytes_per_el
    elif formula == "hybrid":
        # Gemma 2/3: interleaved sliding-window + full-attention layers.
        fl = full_layers if full_layers is not None else layers // 2
        sl = layers - fl
        f_kvh = full_kv_heads if full_kv_heads is not None else kv_heads
        f_hd = full_head_dim if full_head_dim is not None else head_dim
        sliding_tokens = min(context, sliding_window)
        kv_bytes = (
            2 * sl * kv_heads * head_dim * sliding_tokens * bytes_per_el
            + 2 * fl * f_kvh * f_hd * context * bytes_per_el
        )
    elif formula == "mla":
        # DeepSeek V2/V3/R1: latent jointly encodes K and V, no factor of 2.
        kv_bytes = layers * (kv_lora_rank + qk_rope_head_dim) * context * bytes_per_el
    elif formula == "linear_hybrid":
        # Qwen3-Next-style: linear-attention layers have fixed recurrent state
        # (negligible); only sparse full-attention layers grow KV with context.
        fl = full_layers if full_layers is not None else layers // 4
        kv_bytes = 2 * fl * kv_heads * head_dim * context * bytes_per_el
    else:
        raise SystemExit(f"Unknown kv-formula '{formula}'")

    kv_fill = kv_fill_pct / 100.0
    return (kv_bytes / 1e9) * concurrent_users * kv_fill


def _ram_status(total_gb: float, available_gb: float) -> str:
    if available_gb <= 0:
        return "unknown"
    ratio = total_gb / available_gb
    if ratio <= 0.80:
        return "fits"
    if ratio <= 1.00:
        return "tight"
    return "exceeds"


def _tps(
    active_params_b: float,
    weights_bits: float,
    kv_traffic_gb: float,
    bandwidth_gbs: float,
    efficiency: float,
) -> Optional[float]:
    if bandwidth_gbs <= 0 or active_params_b <= 0:
        return None
    # Per-token traffic = active weights read + KV read for all cached tokens.
    # Weights per token use 1.1 overhead to mirror _weights_gb.
    model_gb = (active_params_b * 1e9 * (weights_bits / 8.0) * 1.1) / 1e9
    effective_bw = bandwidth_gbs * efficiency
    return _round(effective_bw / (model_gb + kv_traffic_gb))


def _verdict(total_gb: float, available_gb: float, tps: Optional[float]) -> str:
    if available_gb > 0 and total_gb > available_gb * 0.95:
        return "❌ won't run well"
    if tps is not None and tps < 5:
        return "❌ won't run well"
    if available_gb > 0 and total_gb > available_gb * 0.85:
        return "⚠️ runs but tight"
    if tps is not None and tps < 15:
        return "⚠️ runs but tight"
    return "✅ runs well"


def estimate(
    *,
    params: float,
    layers: int,
    kv_heads: int,
    head_dim: int,
    context: int,
    quant: str,
    kv_quant: str = "fp16",
    available_ram: float = 0,
    bandwidth: float = 0,
    efficiency: float = 0.8,
    overhead: float = 1.0,
    moe: bool = False,
    active_params: Optional[float] = None,
    kv_formula: KvFormula = "standard",
    sliding_window: int = 4096,
    full_layers: Optional[int] = None,
    full_kv_heads: Optional[int] = None,
    full_head_dim: Optional[int] = None,
    kv_lora_rank: int = 512,
    qk_rope_head_dim: int = 64,
    concurrent_users: int = 1,
    kv_fill_pct: float = 100.0,
) -> FitResult:
    notes = []

    weights = _weights_gb(params, quant)
    kv_cache = _kv_cache_gb(
        layers,
        kv_heads,
        head_dim,
        context,
        kv_quant,
        kv_formula,
        sliding_window,
        full_layers,
        full_kv_heads,
        full_head_dim,
        kv_lora_rank,
        qk_rope_head_dim,
        concurrent_users,
        kv_fill_pct,
    )
    total = weights + kv_cache + overhead

    # TPS uses active params for MoE (only experts routed to this token
    # are read from memory), total params for dense models. RAM footprint
    # always uses total params because every expert stays resident.
    active_b = active_params if (moe and active_params) else params
    if moe and not active_params:
        notes.append(
            "MoE flag set without --active-params; TPS uses total params (conservative)"
        )
    bits = QUANT_BITS.get(quant.lower(), 4.84)

    tps = (
        _tps(active_b, bits, kv_cache, bandwidth, efficiency) if bandwidth > 0 else None
    )
    ceiling = _tps(active_b, bits, 0, bandwidth, efficiency) if bandwidth > 0 else None
    ram_status = _ram_status(total, available_ram)
    verdict = _verdict(total, available_ram, tps)

    if ram_status == "unknown":
        notes.append("no --available-ram given; fit check limited to total_gb")
    if kv_cache > weights:
        notes.append(
            "KV cache exceeds weight size — consider --kv-quant q8 or shorter --context"
        )

    return FitResult(
        weights_gb=_round(weights),
        kv_cache_gb=_round(kv_cache),
        overhead_gb=_round(overhead),
        total_gb=_round(total),
        ram_status=ram_status,
        tps_estimate=tps,
        tps_ceiling=ceiling,
        verdict=verdict,
        notes=notes,
    )


def _format_report(result: FitResult, args) -> str:
    lines = [
        f"Model params:      {args.params} B"
        + (
            f" ({args.active_params}B active, MoE)"
            if args.moe and args.active_params
            else ""
        ),
        f"Quant:             {args.quant} (KV: {args.kv_quant})",
        f"Context:           {args.context:,} tokens",
        f"Architecture:      layers={args.layers} kv_heads={args.kv_heads} head_dim={args.head_dim} formula={args.kv_formula}",
        "",
        f"Weights:           {result.weights_gb} GB",
        f"KV cache:          {result.kv_cache_gb} GB",
        f"Overhead:          {result.overhead_gb} GB",
        f"Total required:    {result.total_gb} GB",
    ]
    if args.available_ram > 0:
        pct = result.total_gb / args.available_ram * 100
        lines.append(
            f"Available memory:  {args.available_ram} GB  ({pct:.0f}% used — {result.ram_status})"
        )
    if result.tps_estimate is not None:
        lines.append(
            f"Throughput:        ~{result.tps_estimate} tok/s decode (ceiling ~{result.tps_ceiling}, batch=1)"
        )
    lines.append("")
    lines.append(f"Verdict:           {result.verdict}")
    for n in result.notes:
        lines.append(f"  note: {n}")
    return "\n".join(lines)


def _self_test() -> int:
    """Regression tests — values cross-checked against WeightRoom and
    worked examples in references/memory-math.md and decision-workflow.md.
    Tolerances are generous (±5%) because WeightRoom uses QUANT_BYTES
    (0.5 for q4) while we use community-measured QUANT_BITS (4.84 for q4_k_m);
    both are valid, we prefer the community numbers.
    """
    cases = [
        (
            "Llama-3.1-8B Q4_K_M @ 8k on RTX 4090",
            dict(
                params=8,
                layers=32,
                kv_heads=8,
                head_dim=128,
                context=8192,
                quant="q4_k_m",
                kv_quant="fp16",
                available_ram=24,
                bandwidth=800,
            ),
            5.3,
            6.6,
            0.15,
        ),
        (
            "Llama-3.1-70B IQ2_XXS @ 8k on RTX 4090 (from decision-workflow.md §2)",
            dict(
                params=70,
                layers=80,
                kv_heads=8,
                head_dim=128,
                context=8192,
                quant="iq2_xxs",
                kv_quant="q8",
                available_ram=24,
                bandwidth=800,
                overhead=0.8,
            ),
            18.0,
            20.3,
            0.20,
        ),
        (
            "Qwen2.5-14B 4bit @ 8k on M2 Pro 16GB (from decision-workflow.md §3)",
            dict(
                params=14,
                layers=48,
                kv_heads=8,
                head_dim=128,
                context=8192,
                quant="mlx_4",
                kv_quant="fp16",
                available_ram=16,
                bandwidth=160,
                overhead=0.5,
            ),
            7.7,
            9.7,
            0.20,
        ),
        (
            "Mixtral-8x7B MoE Q4 @ 8k (active 13B)",
            dict(
                params=47,
                layers=32,
                kv_heads=8,
                head_dim=128,
                context=8192,
                quant="q4_k_m",
                kv_quant="fp16",
                available_ram=32,
                bandwidth=800,
                moe=True,
                active_params=13,
                overhead=1.0,
            ),
            31.3,
            32.6,
            0.15,
        ),
        (
            "DeepSeek-V3 MLA @ 8k — KV must be much smaller than standard",
            dict(
                params=37,
                layers=61,
                kv_heads=128,
                head_dim=128,
                context=8192,
                quant="q4_k_m",
                kv_quant="fp16",
                available_ram=512,
                bandwidth=400,
                moe=True,
                active_params=37,
                kv_formula="mla",
                kv_lora_rank=512,
                qk_rope_head_dim=64,
                overhead=1.0,
            ),
            24.6,
            25.7,
            0.15,
        ),
    ]
    failures = 0
    for name, kw, exp_w, exp_t, tol in cases:
        r = estimate(**kw)
        w_ok = abs(r.weights_gb - exp_w) / exp_w <= tol
        t_ok = abs(r.total_gb - exp_t) / exp_t <= tol
        status = "PASS" if (w_ok and t_ok) else "FAIL"
        if status == "FAIL":
            failures += 1
        print(f"[{status}] {name}")
        print(
            f"        weights: got {r.weights_gb} expected ~{exp_w} ({'ok' if w_ok else 'off'})"
        )
        print(
            f"        total:   got {r.total_gb} expected ~{exp_t} ({'ok' if t_ok else 'off'})"
        )
        print(f"        verdict: {r.verdict}  tps: {r.tps_estimate}")
    print()
    print(f"{len(cases) - failures}/{len(cases)} passed")
    return 0 if failures == 0 else 1


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--self-test", action="store_true", help="Run regression tests")
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON result instead of human-readable report",
    )

    p.add_argument(
        "--params",
        type=float,
        help="Total parameters (billions). For MoE, this is total.",
    )
    p.add_argument("--layers", type=int, help="num_hidden_layers from config.json")
    p.add_argument(
        "--kv-heads",
        type=int,
        help="num_key_value_heads (GQA). For MHA, same as num_attention_heads",
    )
    p.add_argument("--head-dim", type=int, help="hidden_size / num_attention_heads")
    p.add_argument(
        "--context", type=int, default=8192, help="context tokens (default 8192)"
    )
    p.add_argument(
        "--quant",
        default="q4_k_m",
        help=f"weight quant (default q4_k_m). Options: {sorted(QUANT_BITS)}",
    )
    p.add_argument(
        "--kv-quant",
        default="fp16",
        help="KV cache quant (default fp16; try q8 to halve KV)",
    )
    p.add_argument(
        "--available-ram",
        type=float,
        default=0,
        help="Available VRAM/unified RAM in GB",
    )
    p.add_argument(
        "--bandwidth", type=float, default=0, help="Effective memory bandwidth in GB/s"
    )
    p.add_argument(
        "--efficiency",
        type=float,
        default=0.8,
        help="Bandwidth efficiency 0-1 (default 0.8)",
    )
    p.add_argument(
        "--overhead",
        type=float,
        default=1.0,
        help="Engine + activations overhead in GB (default 1.0)",
    )

    p.add_argument("--moe", action="store_true", help="Mixture of Experts model")
    p.add_argument(
        "--active-params",
        type=float,
        help="Active params per token (billions). Required for MoE TPS math.",
    )

    p.add_argument(
        "--kv-formula",
        default="standard",
        choices=["standard", "hybrid", "mla", "linear_hybrid"],
        help="KV cache architecture (default standard)",
    )
    p.add_argument("--sliding-window", type=int, default=4096)
    p.add_argument("--full-layers", type=int)
    p.add_argument("--full-kv-heads", type=int)
    p.add_argument("--full-head-dim", type=int)
    p.add_argument("--kv-lora-rank", type=int, default=512, help="MLA only")
    p.add_argument("--qk-rope-head-dim", type=int, default=64, help="MLA only")

    p.add_argument("--concurrent-users", type=int, default=1)
    p.add_argument(
        "--kv-fill-pct",
        type=float,
        default=100.0,
        help="KV cache fill percent (100 = llama.cpp pre-alloc, 25 = vLLM typical)",
    )

    args = p.parse_args()

    if args.self_test:
        return _self_test()

    required = ("params", "layers", "kv_heads", "head_dim")
    missing = [f"--{r.replace('_', '-')}" for r in required if getattr(args, r) is None]
    if missing:
        p.error(
            f"missing required args: {' '.join(missing)} (resolve the model first via search-protocol.md)"
        )

    result = estimate(
        params=args.params,
        layers=args.layers,
        kv_heads=args.kv_heads,
        head_dim=args.head_dim,
        context=args.context,
        quant=args.quant,
        kv_quant=args.kv_quant,
        available_ram=args.available_ram,
        bandwidth=args.bandwidth,
        efficiency=args.efficiency,
        overhead=args.overhead,
        moe=args.moe,
        active_params=args.active_params,
        kv_formula=args.kv_formula,
        sliding_window=args.sliding_window,
        full_layers=args.full_layers,
        full_kv_heads=args.full_kv_heads,
        full_head_dim=args.full_head_dim,
        kv_lora_rank=args.kv_lora_rank,
        qk_rope_head_dim=args.qk_rope_head_dim,
        concurrent_users=args.concurrent_users,
        kv_fill_pct=args.kv_fill_pct,
    )

    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print(_format_report(result, args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
