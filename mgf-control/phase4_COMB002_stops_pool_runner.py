"""
COMB_002_IMPULSE Phase 4 — SuperStop Optimization (Pool Runner)
Optimiza el SuperStop con Signal+Contexto+Exits bloqueados.

Grid: superstop_quality × superstop_coef_volat = 3 × 4 = 12 combos

Optimization ID: OPT-COMB002-{ASSET}-{TF}-PH4-{FECHA}

Uso:
  python3 phase4_COMB002_stops_pool_runner.py --asset ES --timeframe 5m
  python3 phase4_COMB002_stops_pool_runner.py --asset YM --timeframe 10m --workers 8
"""

import argparse
import csv
import json
import sys
from datetime import date
from itertools import product
from multiprocessing import Pool, cpu_count
from pathlib import Path

_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from COMB_002_IMPULSE_V1 import Comb002ImpulseStrategy, Comb002ImpulseParams, load_ohlc_csv

SUPPORTED_ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
SUPPORTED_TIMEFRAMES = ["5m", "10m", "15m"]
ROBUSTNESS_THRESHOLD = 0.80
MIN_TRADES           = 30

# ── Phase 4 Grid ─────────────────────────────────────────────────────────────
SUPERSTOP_QUALITY_RANGE = [1, 2, 3]
SUPERSTOP_COEF_RANGE    = [2.0, 3.0, 4.0, 5.0]


def generate_opt_id(asset: str, timeframe: str) -> str:
    fecha = date.today().strftime("%Y%m%d")
    return f"OPT-COMB002-{asset}-{timeframe}-PH4-{fecha}"


def run_stops_combo(args):
    quality, coef, ph1, ph2a, ph2b, ph3, phase_a_rows, phase_b_rows, opt_id = args

    params = Comb002ImpulseParams(
        # Phase 1 locked
        stpmt_smooth_h=ph1["stpmt_smooth_h"],
        stpmt_smooth_b=ph1["stpmt_smooth_b"],
        stpmt_distance_max_h=ph1["stpmt_distance_max_h"],
        stpmt_distance_max_l=ph1["stpmt_distance_max_l"],
        # Phase 2a locked
        horaire_allowed_hours_utc=ph2a["horaire_allowed_hours_utc"],
        # Phase 2b locked
        volatility_atr_min=ph2b["volatility_atr_min"],
        volatility_atr_max=ph2b["volatility_atr_max"],
        # Phase 3 locked
        scalping_target_coef_volat=ph3["scalping_target_coef_volat"],
        timescan_bars=ph3["timescan_bars"],
        # Phase 4: stops being tested
        superstop_quality=quality,
        superstop_coef_volat=coef,
        # Defaults
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
    )

    strategy = Comb002ImpulseStrategy(params)
    result_a = strategy.run(phase_a_rows)
    result_b = strategy.run(phase_b_rows)

    rob = (result_b.profit_factor / result_a.profit_factor
           if result_a.profit_factor > 0 else 0.0)

    return {
        "optimization_id":  opt_id,
        "superstop_quality": quality,
        "superstop_coef":    coef,
        "phase_a_pf":        round(result_a.profit_factor, 4),
        "phase_a_wr":        round(result_a.win_rate, 4),
        "phase_a_trades":    len(result_a.trades),
        "phase_a_equity":    round(result_a.equity_points, 2),
        "phase_b_pf":        round(result_b.profit_factor, 4),
        "phase_b_wr":        round(result_b.win_rate, 4),
        "phase_b_trades":    len(result_b.trades),
        "phase_b_equity":    round(result_b.equity_points, 2),
        "robustness":        round(rob, 4),
    }


def main():
    parser = argparse.ArgumentParser(
        description="COMB_002 IMPULSE Phase 4 — SuperStop Pool runner"
    )
    parser.add_argument("--asset",     required=True, choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True, choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument("--workers",   type=int, default=None)
    args = parser.parse_args()

    asset     = args.asset
    timeframe = args.timeframe
    workers   = args.workers or cpu_count()
    opt_id    = generate_opt_id(asset, timeframe)

    def load_json(fname):
        p = Path(fname)
        if not p.exists():
            print(f"[ERROR] {fname} not found.")
            sys.exit(1)
        with open(p) as fh:
            return json.load(fh)

    ph1  = load_json(f"COMB002_phase1_{asset}_{timeframe}_best_params.json")
    ph2a = load_json(f"COMB002_phase2a_{asset}_{timeframe}_best_params.json")
    ph2b = load_json(f"COMB002_phase2b_{asset}_{timeframe}_best_params.json")
    ph3  = load_json(f"COMB002_phase3_{asset}_{timeframe}_best_params.json")

    phase_a_file = f"{asset}_phase_A_{timeframe}.csv"
    phase_b_file = f"{asset}_phase_B_{timeframe}.csv"
    for f in [phase_a_file, phase_b_file]:
        if not Path(f).exists():
            print(f"[ERROR] {f} not found.")
            sys.exit(1)

    total = len(SUPERSTOP_QUALITY_RANGE) * len(SUPERSTOP_COEF_RANGE)

    print(f"\n{'='*80}")
    print(f"COMB_002 IMPULSE | Phase 4 SuperStop | {asset} {timeframe}")
    print(f"Optimization ID: {opt_id}")
    print(f"{'='*80}")
    print(f"Workers: {workers} | Grid: {len(SUPERSTOP_QUALITY_RANGE)}×{len(SUPERSTOP_COEF_RANGE)} = {total} combos")
    print(f"Ph1 locked: smooth_h={ph1['stpmt_smooth_h']} smooth_b={ph1['stpmt_smooth_b']} "
          f"dh={ph1['stpmt_distance_max_h']} dl={ph1['stpmt_distance_max_l']}")
    print(f"Ph2a locked: horaire={ph2a['horaire_label']}")
    print(f"Ph2b locked: volatility={ph2b['volatility_label']}")
    print(f"Ph3 locked: scalp_coef={ph3['scalping_target_coef_volat']} timescan={ph3['timescan_bars']}")

    phase_a_rows = load_ohlc_csv(phase_a_file)
    phase_b_rows = load_ohlc_csv(phase_b_file)
    print(f"Phase A: {len(phase_a_rows):,} bars | Phase B: {len(phase_b_rows):,} bars\n")

    all_combos = [
        (q, c, ph1, ph2a, ph2b, ph3, phase_a_rows, phase_b_rows, opt_id)
        for q, c in product(SUPERSTOP_QUALITY_RANGE, SUPERSTOP_COEF_RANGE)
    ]

    results = []
    completed = 0
    best_rob = 0.0

    with Pool(processes=workers) as pool:
        for row in pool.imap_unordered(run_stops_combo, all_combos, chunksize=4):
            results.append(row)
            completed += 1
            if row["robustness"] > best_rob:
                best_rob = row["robustness"]
                flag = ">>> PASS <<<" if best_rob >= ROBUSTNESS_THRESHOLD else ""
                print(f"  [{completed:>2}/{total}] NEW BEST {flag}: "
                      f"quality={row['superstop_quality']} coef={row['superstop_coef']:.1f} | "
                      f"Rob={best_rob:.4f} | "
                      f"PF_A={row['phase_a_pf']:.3f} PF_B={row['phase_b_pf']:.3f} | "
                      f"T_A={row['phase_a_trades']} T_B={row['phase_b_trades']}")
                sys.stdout.flush()

    # Sort: valid trades first
    valid   = [r for r in results if r["phase_a_trades"] >= MIN_TRADES and r["phase_b_trades"] >= MIN_TRADES // 2]
    invalid = [r for r in results if r not in valid]
    valid.sort(key=lambda x: x["robustness"], reverse=True)
    invalid.sort(key=lambda x: x["robustness"], reverse=True)
    results = valid + invalid

    if not valid:
        print(f"\n[WARNING] No combo met MIN_TRADES={MIN_TRADES}. T_A={results[0]['phase_a_trades']} — use with caution.")
    else:
        print(f"\n[INFO] {len(valid)}/{len(results)} combos met MIN_TRADES={MIN_TRADES}.")

    for r in results:
        r["asset"]     = asset
        r["timeframe"] = timeframe

    fields = ["optimization_id", "asset", "timeframe",
              "superstop_quality", "superstop_coef",
              "phase_a_pf", "phase_a_wr", "phase_a_trades", "phase_a_equity",
              "phase_b_pf", "phase_b_wr", "phase_b_trades", "phase_b_equity",
              "robustness"]

    log_file = f"COMB002_phase4_{asset}_{timeframe}_stops_log.csv"
    with open(log_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    print(f"[OK] {log_file}")

    best = results[0]
    best_params = {
        "optimization_id":           opt_id,
        "strategy":                  "COMB_002_IMPULSE",
        "asset":                     asset,
        "timeframe":                 timeframe,
        "phase":                     "4",
        # All previous phases locked
        "stpmt_smooth_h":            ph1["stpmt_smooth_h"],
        "stpmt_smooth_b":            ph1["stpmt_smooth_b"],
        "stpmt_distance_max_h":      ph1["stpmt_distance_max_h"],
        "stpmt_distance_max_l":      ph1["stpmt_distance_max_l"],
        "horaire_label":             ph2a["horaire_label"],
        "horaire_allowed_hours_utc": ph2a["horaire_allowed_hours_utc"],
        "volatility_label":          ph2b["volatility_label"],
        "volatility_atr_min":        ph2b["volatility_atr_min"],
        "volatility_atr_max":        ph2b["volatility_atr_max"],
        "scalping_target_coef_volat": ph3["scalping_target_coef_volat"],
        "timescan_bars":             ph3["timescan_bars"],
        # Phase 4 best
        "superstop_quality":         best["superstop_quality"],
        "superstop_coef_volat":      best["superstop_coef"],
        "robustness":                best["robustness"],
        "phase_a_pf":                best["phase_a_pf"],
        "phase_b_pf":                best["phase_b_pf"],
        "phase_a_trades":            best["phase_a_trades"],
        "phase_b_trades":            best["phase_b_trades"],
        "robustness_pass":           best["robustness"] >= ROBUSTNESS_THRESHOLD,
        "min_trades_pass":           best["phase_a_trades"] >= MIN_TRADES,
        "phase_ids": {
            "phase1": f"OPT-COMB002-{asset}-{timeframe}-PH1-20260424",
            "phase2a": f"OPT-COMB002-{asset}-{timeframe}-PH2a-20260424",
            "phase2b": f"OPT-COMB002-{asset}-{timeframe}-PH2b-20260424",
            "phase3": f"OPT-COMB002-{asset}-{timeframe}-PH3-20260424",
            "phase4": opt_id,
        }
    }

    best_file = f"COMB002_phase4_{asset}_{timeframe}_best_params.json"
    with open(best_file, "w") as fh:
        json.dump(best_params, fh, indent=2)
    print(f"[OK] {best_file}")

    status = ">>> PASS <<<" if best["robustness"] >= ROBUSTNESS_THRESHOLD else "!!! FAIL !!!"
    print(f"\n{'='*80}")
    print(f"PHASE 4 DONE: {asset} {timeframe} [{status}]")
    print(f"  ID:                  {opt_id}")
    print(f"  superstop_quality  = {best['superstop_quality']}")
    print(f"  superstop_coef     = {best['superstop_coef']}")
    print(f"  robustness         = {best['robustness']:.4f}")
    print(f"  phase_a_pf         = {best['phase_a_pf']:.4f}")
    print(f"  phase_b_pf         = {best['phase_b_pf']:.4f}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
