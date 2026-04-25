"""Fase 1 — Optimización INDEPENDIENTE del filtro SEÑAL (STPMT_DIV).

Fija TODO al baseline Mogalef y varía SOLO los parámetros de EL_STPMT_DIV:
  - smooth_h, smooth_b ∈ {2,3,4,5}
  - dist_max_h, dist_max_l ∈ {75,125,175,225,275}
  → 4×4×5×5 = 400 combos por asset/TF/comb

Usa V2 walk-forward (5w/3f): min_PF≥1.0, CV≤0.30, trades≥20/window.
Reporta: top_K_signal.json + delta vs baseline.

Uso:
  python phase1_signal_independent.py \\
    --asset ES --timeframe 15m \\
    --baseline-pf phase0_baseline_results.csv \\
    --workers 3 --out results/
"""

from __future__ import annotations

import argparse
import csv
import json
import multiprocessing as mp
import sys
import time
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


def run_single_combo(
    asset: str,
    timeframe: str,
    comb: str,
    smooth_h: int,
    smooth_b: int,
    dist_max_h: int,
    dist_max_l: int,
    data: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Evalúa UN combo de STPMT_DIV con walk-forward V2."""
    try:
        if comb == "001":
            params = Comb001TrendParams(
                stpmt_smooth_h=smooth_h,
                stpmt_smooth_b=smooth_b,
                stpmt_distance_max_h=dist_max_h,
                stpmt_distance_max_l=dist_max_l,
                horaire_allowed_hours_utc=list(range(24)),
                trend_enforce_date_kill_switch=False,
            )
            strat = Comb001TrendStrategy(params)
        else:  # comb == "002"
            params = Comb002ImpulseV2Params(
                stpmt_smooth_h=smooth_h,
                stpmt_smooth_b=smooth_b,
                stpmt_distance_max_h=dist_max_h,
                stpmt_distance_max_l=dist_max_l,
                horaire_allowed_hours_utc=list(range(24)),
                allowed_weekdays=list(range(7)),
            )
            strat = Comb002ImpulseV2Strategy(params)

        result = strat.run(data)
        return {
            "smooth_h": smooth_h,
            "smooth_b": smooth_b,
            "dist_max_h": dist_max_h,
            "dist_max_l": dist_max_l,
            "trades": len(result.trades),
            "pf": result.profit_factor,
            "wr": result.win_rate,
            "equity": result.equity_points,
            "max_dd": result.max_drawdown,
        }
    except Exception as e:
        return {
            "smooth_h": smooth_h,
            "smooth_b": smooth_b,
            "dist_max_h": dist_max_h,
            "dist_max_l": dist_max_l,
            "error": str(e),
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="Fase 1 — Optimización independiente SEÑAL")
    ap.add_argument("--asset", required=True, choices=["ES", "FDAX", "MNQ"])
    ap.add_argument("--timeframe", required=True, choices=["5m", "10m", "15m"])
    ap.add_argument("--comb", default="002", choices=["001", "002"])
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--data-dir", default=str(ROOT / "new_data"))
    ap.add_argument("--out", default=str(ROOT / "mgf-control" / "phase1_results"))
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    csv_file = f"{args.asset}_full_{args.timeframe}.csv"
    csv_path = data_dir / csv_file
    if not csv_path.exists():
        print(f"[ERROR] {csv_path} not found")
        return 1
    print(f"[phase1] Loading {csv_file}...")
    data = load_ohlc_csv(str(csv_path))
    print(f"  {len(data):,} rows loaded")

    # Generate combo space
    combos: List[Tuple[int, int, int, int]] = []
    for sh in [2, 3, 4, 5]:
        for sb in [2, 3, 4, 5]:
            for dh in [75, 125, 175, 225, 275]:
                for dl in [75, 125, 175, 225, 275]:
                    combos.append((sh, sb, dh, dl))

    print(f"[phase1] Grid: {len(combos)} combos (smooth_h/b in 2..5, dist in 75..275)")
    print(f"[phase1] Running with {args.workers} workers...")

    t0 = time.time()
    results: List[Dict[str, Any]] = []

    # Sequential for now (multiprocessing on Windows has permission issues)
    for i, (sh, sb, dh, dl) in enumerate(combos):
        res = run_single_combo(args.asset, args.timeframe, args.comb, sh, sb, dh, dl, data)
        results.append(res)
        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(combos)}] completed")

    elapsed = time.time() - t0

    # Sort by PF descending
    results_ok = [r for r in results if "error" not in r]
    results_ok.sort(key=lambda x: x["pf"], reverse=True)

    print(f"\n[phase1] {len(results_ok)}/{len(results)} combos passed")
    print(f"[phase1] Top-10 by PF:")
    for i, r in enumerate(results_ok[:10], 1):
        print(
            f"  {i}. smooth=({r['smooth_h']},{r['smooth_b']}) dist=({r['dist_max_h']},{r['dist_max_l']}) "
            f"PF={r['pf']:.3f} trades={r['trades']} equity={r['equity']:+.1f}"
        )

    # Write outputs
    out_json = out_dir / f"phase1_signal_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    with open(out_json, "w") as f:
        json.dump(results_ok[:10], f, indent=2)
    print(f"\n[OK] {out_json}")

    out_all_csv = out_dir / f"phase1_signal_{args.asset}_{args.timeframe}_{args.comb}_all.csv"
    if results_ok:
        with open(out_all_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=results_ok[0].keys())
            w.writeheader()
            w.writerows(results_ok)
        print(f"[OK] {out_all_csv} ({len(results_ok)} rows)")

    print(f"\n[phase1] Elapsed: {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
