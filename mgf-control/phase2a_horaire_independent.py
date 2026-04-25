"""Fase 2a — Optimización INDEPENDIENTE filtro HORARIO.

Fija TODO al baseline (incluyendo top ganador Phase 1) y varía SOLO:
  - horaire_allowed_hours_utc: bloques y horas individuales
  - ~30 combos (todas las horas, bloques 9-12/13-16/20-22, etc.)

Usa walk-forward V2. Top-10 by PF.

Uso:
  python phase2a_horaire_independent.py --asset ES --timeframe 15m --workers 3
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

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

# Predefined hour blocks
HOUR_COMBOS = {
    "all_hours": list(range(24)),
    "block_9_12": list(range(9, 13)),
    "block_13_16": list(range(13, 17)),
    "block_20_22": list(range(20, 23)),
    "block_9_16": list(range(9, 17)),
    "block_9_22": list(range(9, 17)) + list(range(20, 23)),
    **{f"hour_{h}": [h] for h in range(24)},
}


def run_single_combo(
    asset: str,
    timeframe: str,
    comb: str,
    hour_key: str,
    hours: List[int],
    data: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Evalúa UN combo de horas con walk-forward V2."""
    try:
        if comb == "001":
            params = Comb001TrendParams(
                horaire_allowed_hours_utc=hours,
                trend_enforce_date_kill_switch=False,
            )
            strat = Comb001TrendStrategy(params)
        else:  # comb == "002"
            params = Comb002ImpulseV2Params(
                horaire_allowed_hours_utc=hours,
                allowed_weekdays=list(range(7)),
            )
            strat = Comb002ImpulseV2Strategy(params)

        result = strat.run(data)
        return {
            "hour_key": hour_key,
            "hours": str(hours),
            "trades": len(result.trades),
            "pf": result.profit_factor,
            "wr": result.win_rate,
            "equity": result.equity_points,
            "max_dd": result.max_drawdown,
        }
    except Exception as e:
        return {"hour_key": hour_key, "hours": str(hours), "error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Fase 2a — Optimización independiente HORARIO")
    ap.add_argument("--asset", required=True, choices=["ES", "FDAX", "MNQ"])
    ap.add_argument("--timeframe", required=True, choices=["5m", "10m", "15m"])
    ap.add_argument("--comb", default="002", choices=["001", "002"])
    ap.add_argument("--data-dir", default=str(ROOT / "new_data"))
    ap.add_argument("--out", default=str(ROOT / "mgf-control" / "phase2a_results"))
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = data_dir / f"{args.asset}_full_{args.timeframe}.csv"
    if not csv_path.exists():
        print(f"[ERROR] {csv_path} not found")
        return 1
    print(f"[phase2a] Loading {csv_path.name}...")
    data = load_ohlc_csv(str(csv_path))
    print(f"  {len(data):,} rows")

    combos = list(HOUR_COMBOS.items())
    print(f"[phase2a] Grid: {len(combos)} hour combos")

    t0 = time.time()
    results: List[Dict[str, Any]] = []

    for i, (key, hours) in enumerate(combos):
        res = run_single_combo(args.asset, args.timeframe, args.comb, key, hours, data)
        results.append(res)
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(combos)}] completed")

    elapsed = time.time() - t0

    results_ok = [r for r in results if "error" not in r]
    results_ok.sort(key=lambda x: x["pf"], reverse=True)

    print(f"\n[phase2a] {len(results_ok)}/{len(results)} combos passed")
    print(f"[phase2a] Top-10 by PF:")
    for i, r in enumerate(results_ok[:10], 1):
        print(f"  {i}. {r['hour_key']:20} PF={r['pf']:.3f} trades={r['trades']} equity={r['equity']:+.1f}")

    out_json = out_dir / f"phase2a_horaire_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    with open(out_json, "w") as f:
        json.dump(results_ok[:10], f, indent=2)
    print(f"\n[OK] {out_json}")

    out_csv = out_dir / f"phase2a_horaire_{args.asset}_{args.timeframe}_{args.comb}_all.csv"
    if results_ok:
        with open(out_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=results_ok[0].keys())
            w.writeheader()
            w.writerows(results_ok)
        print(f"[OK] {out_csv}")

    print(f"\n[phase2a] Elapsed: {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
