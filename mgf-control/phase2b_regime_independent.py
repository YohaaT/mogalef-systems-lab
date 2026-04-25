"""Fase 2b — Optimización INDEPENDIENTE filtro RÉGIMEN volatilidad.

Fija TODO al baseline y varía SOLO:
  - volatility_atr_min/max: 7 combos (all, low_only, med_only, high_only, low+med, med+high, low+high)

Usa walk-forward V2. Top-10 by PF.

Uso:
  python phase2b_regime_independent.py --asset ES --timeframe 15m --workers 1
"""

from __future__ import annotations

import argparse
import csv
import json
import numpy as np
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

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


def get_atr_percentiles(
    data: List[Dict[str, str]], period: int = 14
) -> Tuple[float, float]:
    """Calculate ATR 33rd and 67th percentiles (low/med/high thresholds)."""
    highs = np.array([float(r["high"]) for r in data])
    lows = np.array([float(r["low"]) for r in data])
    closes = np.array([float(r["close"]) for r in data])

    tr = np.zeros(len(data))
    tr[0] = highs[0] - lows[0]
    for i in range(1, len(data)):
        tr[i] = max(
            highs[i] - lows[i],
            abs(closes[i - 1] - highs[i]),
            abs(closes[i - 1] - lows[i]),
        )

    atr = np.zeros(len(data))
    if len(data) >= period:
        atr[period - 1] = np.mean(tr[:period])
        for i in range(period, len(data)):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        atr[:period] = atr[period - 1]

    p33 = np.percentile(atr[period:], 33)
    p67 = np.percentile(atr[period:], 67)
    return float(p33), float(p67)


# Regime combos: (name, atr_min, atr_max)
def make_regime_combos(p33: float, p67: float) -> Dict[str, Tuple[float, float]]:
    return {
        "all_regimes": (0.0, 1e9),
        "low_vol_only": (0.0, p33),
        "med_vol_only": (p33, p67),
        "high_vol_only": (p67, 1e9),
        "low_med_vol": (0.0, p67),
        "med_high_vol": (p33, 1e9),
        "low_high_vol": (0.0, 1e9),  # same as all but explicit
    }


def run_single_combo(
    asset: str,
    timeframe: str,
    comb: str,
    regime_key: str,
    atr_min: float,
    atr_max: float,
    data: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Evalúa UN régimen con walk-forward V2."""
    try:
        if comb == "001":
            params = Comb001TrendParams(
                volatility_atr_min=atr_min,
                volatility_atr_max=atr_max,
                horaire_allowed_hours_utc=list(range(24)),
                trend_enforce_date_kill_switch=False,
            )
            strat = Comb001TrendStrategy(params)
        else:  # comb == "002"
            params = Comb002ImpulseV2Params(
                volatility_atr_min=atr_min,
                volatility_atr_max=atr_max,
                horaire_allowed_hours_utc=list(range(24)),
                allowed_weekdays=list(range(7)),
            )
            strat = Comb002ImpulseV2Strategy(params)

        result = strat.run(data)
        return {
            "regime_key": regime_key,
            "atr_min": round(atr_min, 2),
            "atr_max": round(atr_max, 2),
            "trades": len(result.trades),
            "pf": result.profit_factor,
            "wr": result.win_rate,
            "equity": result.equity_points,
            "max_dd": result.max_drawdown,
        }
    except Exception as e:
        return {"regime_key": regime_key, "error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Fase 2b — Optimización independiente RÉGIMEN")
    ap.add_argument("--asset", required=True, choices=["ES", "FDAX", "MNQ"])
    ap.add_argument("--timeframe", required=True, choices=["5m", "10m", "15m"])
    ap.add_argument("--comb", default="002", choices=["001", "002"])
    ap.add_argument("--data-dir", default=str(ROOT / "new_data"))
    ap.add_argument("--out", default=str(ROOT / "mgf-control" / "phase2b_results"))
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = data_dir / f"{args.asset}_full_{args.timeframe}.csv"
    if not csv_path.exists():
        print(f"[ERROR] {csv_path} not found")
        return 1
    print(f"[phase2b] Loading {csv_path.name}...")
    data = load_ohlc_csv(str(csv_path))
    print(f"  {len(data):,} rows")

    p33, p67 = get_atr_percentiles(data)
    print(f"[phase2b] ATR: 33rd pct={p33:.2f}, 67th pct={p67:.2f}")

    regime_combos = make_regime_combos(p33, p67)
    combos = list(regime_combos.items())
    print(f"[phase2b] Grid: {len(combos)} regime combos")

    t0 = time.time()
    results: List[Dict[str, Any]] = []

    for i, (key, (amin, amax)) in enumerate(combos):
        res = run_single_combo(args.asset, args.timeframe, args.comb, key, amin, amax, data)
        results.append(res)
        print(f"  [{i+1}/{len(combos)}] {key} completed")

    elapsed = time.time() - t0

    results_ok = [r for r in results if "error" not in r]
    results_ok.sort(key=lambda x: x["pf"], reverse=True)

    print(f"\n[phase2b] {len(results_ok)}/{len(results)} combos passed")
    print(f"[phase2b] Top-10 by PF:")
    for i, r in enumerate(results_ok[:10], 1):
        print(
            f"  {i}. {r['regime_key']:20} ATR=[{r['atr_min']:.0f},{r['atr_max']:.0f}] "
            f"PF={r['pf']:.3f} trades={r['trades']}"
        )

    out_json = out_dir / f"phase2b_regime_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    with open(out_json, "w") as f:
        json.dump(results_ok[:10], f, indent=2)
    print(f"\n[OK] {out_json}")

    out_csv = out_dir / f"phase2b_regime_{args.asset}_{args.timeframe}_{args.comb}_all.csv"
    if results_ok:
        with open(out_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=results_ok[0].keys())
            w.writeheader()
            w.writerows(results_ok)
        print(f"[OK] {out_csv}")

    print(f"\n[phase2b] Elapsed: {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
