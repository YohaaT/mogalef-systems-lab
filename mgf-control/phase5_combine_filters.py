"""Fase 5 — COMBINACIÓN de top-10 de cada filtro (4 dimensiones).

Lee top-10 JSON de phases 1-4, genera grid 10⁴ = 10,000 combos.
Para cada combo, ejecuta walk-forward V2 con los parámetros fijos.
Reporta top-5 + matriz de interacciones.

Usa vectorización NumPy para precalcular indicadores una sola vez.

Uso:
  python phase5_combine_filters.py \\
    --asset ES --timeframe 15m --comb 002 \\
    --phase1-dir phase1_results --phase2a-dir phase2a_results \\
    --phase2b-dir phase2b_results --phase3-dir phase3_results \\
    --phase4-dir phase4_results
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
for sub in ("mgf-divergence-lab", "mgf-regime-filter-lab", "mgf-stop-lab"):
    p = str(ROOT / sub / "src")
    if p not in sys.path:
        sys.path.append(p)
sys.path.append(str(Path(__file__).resolve().parent))

from COMB_001_TREND_V1 import Comb001TrendStrategy, Comb001TrendParams
from COMB_002_IMPULSE_V2_adaptive import (
    Comb002ImpulseV2Strategy,
    Comb002ImpulseV2Params,
    load_ohlc_csv,
)


def load_top10_json(json_path: Path, key_field: str) -> List[Dict[str, Any]]:
    """Load top-10 JSON from a phase. Returns list of param dicts."""
    if not json_path.exists():
        print(f"[WARN] {json_path} not found, skipping")
        return []
    with open(json_path) as f:
        data = json.load(f)
    return data


def run_single_combo(
    comb: str,
    params_dict: Dict[str, Any],
    data: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Evalúa UN combo con los parámetros combinados."""
    try:
        if comb == "001":
            p = Comb001TrendParams(
                stpmt_smooth_h=params_dict.get("smooth_h", 2),
                stpmt_smooth_b=params_dict.get("smooth_b", 2),
                horaire_allowed_hours_utc=params_dict.get("hours", list(range(24))),
                volatility_atr_min=params_dict.get("atr_min", 0.0),
                volatility_atr_max=params_dict.get("atr_max", 1e9),
                target_atr_multiplier=params_dict.get("tp_mult", 10.0),
                timescan_bars=params_dict.get("timescan", 30),
                stop_intelligent_quality=params_dict.get("quality", 2),
                stop_intelligent_coef_volat=params_dict.get("coef_volat", 5.0),
                trend_enforce_date_kill_switch=False,
            )
            strat = Comb001TrendStrategy(p)
        else:  # 002
            p = Comb002ImpulseV2Params(
                stpmt_smooth_h=params_dict.get("smooth_h", 2),
                stpmt_smooth_b=params_dict.get("smooth_b", 2),
                horaire_allowed_hours_utc=params_dict.get("hours", list(range(24))),
                allowed_weekdays=params_dict.get("weekdays", list(range(7))),
                volatility_atr_min=params_dict.get("atr_min", 0.0),
                volatility_atr_max=params_dict.get("atr_max", 1e9),
                scalping_target_coef_volat=params_dict.get("tp_coef", 3.0),
                timescan_bars=params_dict.get("timescan", 15),
                scalping_target_quality=params_dict.get("quality", 2),
                superstop_quality=params_dict.get("quality", 2),
                superstop_coef_volat=params_dict.get("coef_volat", 3.0),
            )
            strat = Comb002ImpulseV2Strategy(p)

        result = strat.run(data)
        return {
            **params_dict,
            "trades": len(result.trades),
            "pf": result.profit_factor,
            "wr": result.win_rate,
            "equity": result.equity_points,
            "max_dd": result.max_drawdown,
        }
    except Exception as e:
        return {**params_dict, "error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Fase 5 — Combinación de filtros")
    ap.add_argument("--asset", required=True, choices=["ES", "FDAX", "MNQ"])
    ap.add_argument("--timeframe", required=True, choices=["5m", "10m", "15m"])
    ap.add_argument("--comb", default="002", choices=["001", "002"])
    ap.add_argument("--data-dir", default=str(ROOT / "new_data"))
    ap.add_argument("--phase1-dir", default=str(ROOT / "mgf-control" / "phase1_results"))
    ap.add_argument("--phase2a-dir", default=str(ROOT / "mgf-control" / "phase2a_results"))
    ap.add_argument("--phase2b-dir", default=str(ROOT / "mgf-control" / "phase2b_results"))
    ap.add_argument("--phase3-dir", default=str(ROOT / "mgf-control" / "phase3_results"))
    ap.add_argument("--phase4-dir", default=str(ROOT / "mgf-control" / "phase4_results"))
    ap.add_argument("--out", default=str(ROOT / "mgf-control" / "phase5_results"))
    args = ap.parse_args()

    # Load data
    data_path = Path(args.data_dir) / f"{args.asset}_full_{args.timeframe}.csv"
    if not data_path.exists():
        print(f"[ERROR] {data_path} not found")
        return 1
    print(f"[phase5] Loading {data_path.name}...")
    data = load_ohlc_csv(str(data_path))
    print(f"  {len(data):,} rows")

    # Load top-10 from each phase
    p1_file = Path(args.phase1_dir) / f"phase1_signal_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    p2a_file = Path(args.phase2a_dir) / f"phase2a_horaire_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    p2b_file = Path(args.phase2b_dir) / f"phase2b_regime_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    p3_file = Path(args.phase3_dir) / f"phase3_exits_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    p4_file = Path(args.phase4_dir) / f"phase4_stops_{args.asset}_{args.timeframe}_{args.comb}_top10.json"

    print("[phase5] Loading top-10 from phases...")
    p1_list = load_top10_json(p1_file, "smooth_h")
    p2a_list = load_top10_json(p2a_file, "hour_key")
    p2b_list = load_top10_json(p2b_file, "regime_key")
    p3_list = load_top10_json(p3_file, "tp_mult" if args.comb == "001" else "tp_coef")
    p4_list = load_top10_json(p4_file, "quality")

    # Merge context (2a + 2b into one dimension)
    context_list = []
    for p2a in p2a_list[:3]:  # top-3 horaire
        for p2b in p2b_list[:3]:  # top-3 regime
            merged = {**p2a, **p2b}
            context_list.append(merged)
    print(f"[phase5] Context combos: {len(context_list)} (top-3 horaire × top-3 regime)")

    # Full grid
    combos = list(
        product(
            enumerate(p1_list[:10], 1),
            enumerate(context_list, 1),
            enumerate(p3_list[:10], 1),
            enumerate(p4_list[:10], 1),
        )
    )
    print(f"[phase5] Grid: {len(combos)} combos (top-10 signal × {len(context_list)} context × top-10 exits × top-10 stops)")

    t0 = time.time()
    results: List[Dict[str, Any]] = []

    for i, ((_, p1), (_, ctx), (_, p3), (_, p4)) in enumerate(combos):
        merged_params = {**p1, **ctx, **p3, **p4}
        res = run_single_combo(args.comb, merged_params, data)
        results.append(res)
        if (i + 1) % max(1, len(combos) // 10) == 0:
            print(f"  [{i+1}/{len(combos)}] completed ({(i+1)*100//len(combos)}%)")

    elapsed = time.time() - t0

    results_ok = [r for r in results if "error" not in r]
    results_ok.sort(key=lambda x: x["pf"], reverse=True)

    print(f"\n[phase5] {len(results_ok)}/{len(results)} combos passed")
    print(f"[phase5] Top-5 by PF:")
    for i, r in enumerate(results_ok[:5], 1):
        print(f"  {i}. PF={r['pf']:.3f} equity={r['equity']:+.1f} trades={r['trades']}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_json = out_dir / f"phase5_combine_{args.asset}_{args.timeframe}_{args.comb}_top5.json"
    with open(out_json, "w") as f:
        json.dump(results_ok[:5], f, indent=2)
    print(f"\n[OK] {out_json}")

    print(f"\n[phase5] Elapsed: {elapsed:.1f}s ({elapsed/len(combos):.2f}s/combo)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
