"""Fase 0 - Baseline Mogalef SIN restricciones temporales.

Corre COMB_001 (TENDANCE) y COMB_002 V2 ADAPTIVE (IMPULSION) sobre los 9
datasets de new_data/, usando los defaults Mogalef base con:
  - horaire_allowed_hours_utc = range(0, 24)   (todas las horas)
  - allowed_weekdays = range(0, 7)             (todos los dias) [solo COMB_002]
  - filtros de volatilidad esencialmente OFF (rangos amplios)
  - COMB_001: trend filter ON, ATR filter ON   (per Mogalef spec)
  - COMB_002: trend filter OFF, ATR filter OFF (per Mogalef spec) + scalping target adaptativo

Output: phase0_baseline_results.csv con (asset, tf, comb, trades, PF, WR, equity, max_dd, exits).
Sirve como punto de comparacion para todas las fases independientes (1-4).

Uso:
  python phase0_baseline_no_temporal.py --data-dir ../new_data --out phase0_baseline_results.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
for sub in ("mgf-divergence-lab", "mgf-regime-filter-lab", "mgf-stop-lab"):
    p = str(ROOT / sub / "src")
    if p not in sys.path:
        sys.path.append(p)
sys.path.append(str(Path(__file__).resolve().parent))

from COMB_001_TREND_V1 import Comb001TrendStrategy, Comb001TrendParams  # type: ignore
from COMB_002_IMPULSE_V2_adaptive import (  # type: ignore
    Comb002ImpulseV2Strategy,
    Comb002ImpulseV2Params,
    load_ohlc_csv,
)


DATASETS = [
    ("ES", "5m", "ES_full_5m.csv"),
    ("ES", "10m", "ES_full_10m.csv"),
    ("ES", "15m", "ES_full_15m.csv"),
    ("FDAX", "5m", "FDAX_full_5m.csv"),
    ("FDAX", "10m", "FDAX_full_10m.csv"),
    ("FDAX", "15m", "FDAX_full_15m.csv"),
    ("MNQ", "5m", "MNQ_full_5m.csv"),
    ("MNQ", "10m", "MNQ_full_10m.csv"),
    ("MNQ", "15m", "MNQ_full_15m.csv"),
]


def make_comb001_baseline() -> Comb001TrendParams:
    """COMB_001 TENDANCE baseline: trend filter ON + ATR filter ON; horaire OFF."""
    return Comb001TrendParams(
        horaire_allowed_hours_utc=list(range(24)),
        volatility_atr_min=0.0,
        volatility_atr_max=1.0e9,
        trend_enforce_date_kill_switch=False,
    )


def make_comb002_baseline() -> Comb002ImpulseV2Params:
    """COMB_002 IMPULSION baseline: NO trend, NO ATR filter, NO horaire, NO day."""
    return Comb002ImpulseV2Params(
        horaire_allowed_hours_utc=list(range(24)),
        allowed_weekdays=list(range(7)),
        volatility_atr_min=0.0,
        volatility_atr_max=1.0e9,
    )


def run_comb001(rows: List[Dict[str, str]]) -> Dict[str, float]:
    strat = Comb001TrendStrategy(make_comb001_baseline())
    res = strat.run(rows)
    return {
        "trades": len(res.trades),
        "equity": float(res.equity_points),
        "pf": float(res.profit_factor),
        "wr": float(res.win_rate),
        "max_dd": float(res.max_drawdown),
        "exits": dict(res.exit_reason_breakdown),
    }


def run_comb002(rows: List[Dict[str, str]]) -> Dict[str, float]:
    strat = Comb002ImpulseV2Strategy(make_comb002_baseline())
    res = strat.run(rows)
    return {
        "trades": len(res.trades),
        "equity": float(res.equity_points),
        "pf": float(res.profit_factor),
        "wr": float(res.win_rate),
        "max_dd": float(res.max_drawdown),
        "exits": dict(res.exit_reason_breakdown),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(ROOT / "new_data"))
    ap.add_argument("--out", default=str(ROOT / "mgf-control" / "phase0_baseline_results.csv"))
    ap.add_argument("--combs", default="001,002", help="comma-separated subset: 001,002")
    ap.add_argument("--datasets", default="ALL", help="comma-separated names like 'MNQ_15m,ES_15m' or 'ALL'")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    combs_to_run = set(c.strip() for c in args.combs.split(","))

    if args.datasets.upper() == "ALL":
        selected = DATASETS
    else:
        wanted = set(s.strip() for s in args.datasets.split(","))
        selected = [d for d in DATASETS if f"{d[0]}_{d[1]}" in wanted]

    rows_out: List[Dict[str, object]] = []
    print(f"[phase0] datasets={len(selected)}  combs={sorted(combs_to_run)}")
    print(f"[phase0] data_dir={data_dir}")

    for asset, tf, fname in selected:
        csv_path = data_dir / fname
        if not csv_path.exists():
            print(f"  [SKIP] {fname} not found")
            continue

        t0 = time.time()
        data = load_ohlc_csv(str(csv_path))
        load_secs = time.time() - t0
        print(f"\n[{asset} {tf}] loaded {len(data):,} rows in {load_secs:.1f}s")

        if "001" in combs_to_run:
            t1 = time.time()
            try:
                m = run_comb001(data)
                dt = time.time() - t1
                print(f"  COMB_001  trades={m['trades']:>5}  PF={m['pf']:.3f}  WR={m['wr']:.1%}  "
                      f"eq={m['equity']:>+9.1f}  dd={m['max_dd']:>6.1f}  ({dt:.1f}s)")
                rows_out.append({
                    "asset": asset, "tf": tf, "comb": "001",
                    "trades": m["trades"], "pf": m["pf"], "wr": m["wr"],
                    "equity": m["equity"], "max_dd": m["max_dd"],
                    "exits_json": json.dumps(m["exits"]),
                    "elapsed_secs": round(dt, 1),
                })
            except Exception as e:
                print(f"  COMB_001  ERROR: {e}")
                rows_out.append({"asset": asset, "tf": tf, "comb": "001", "error": str(e)})

        if "002" in combs_to_run:
            t1 = time.time()
            try:
                m = run_comb002(data)
                dt = time.time() - t1
                print(f"  COMB_002  trades={m['trades']:>5}  PF={m['pf']:.3f}  WR={m['wr']:.1%}  "
                      f"eq={m['equity']:>+9.1f}  dd={m['max_dd']:>6.1f}  ({dt:.1f}s)")
                rows_out.append({
                    "asset": asset, "tf": tf, "comb": "002",
                    "trades": m["trades"], "pf": m["pf"], "wr": m["wr"],
                    "equity": m["equity"], "max_dd": m["max_dd"],
                    "exits_json": json.dumps(m["exits"]),
                    "elapsed_secs": round(dt, 1),
                })
            except Exception as e:
                print(f"  COMB_002  ERROR: {e}")
                rows_out.append({"asset": asset, "tf": tf, "comb": "002", "error": str(e)})

    # Write CSV
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["asset", "tf", "comb", "trades", "pf", "wr", "equity", "max_dd", "exits_json", "elapsed_secs", "error"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows_out:
            w.writerow({k: r.get(k, "") for k in fieldnames})
    print(f"\n[OK] wrote {out_path} ({len(rows_out)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
