"""
COMB_002_IMPULSE Phase 3 — Exits Optimization (Pool Runner)
Optimiza los parámetros de salida con Signal (Ph1) + Contexto (Ph2a+2b) bloqueados.

Exits en COMB_002_IMPULSE:
  - scalping_target_coef_volat : multiplicador ATR para el target de scalping
  - timescan_bars              : barras máximas antes de salida forzada

Grid: 5 × 5 = 25 combinaciones

Optimization ID: OPT-COMB002-{ASSET}-{TF}-PH3-{FECHA}

Uso:
  python3 phase3_COMB002_exits_pool_runner.py --asset ES --timeframe 5m
  python3 phase3_COMB002_exits_pool_runner.py --asset YM --timeframe 10m --workers 8
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

# ── Phase 3 Grid ─────────────────────────────────────────────────────────────
SCALPING_COEF_RANGE = [1.5, 2.0, 3.0, 4.0, 5.0]   # ATR multiplier for target
TIMESCAN_RANGE      = [10, 12, 15, 18, 20]          # bars before forced exit

# ── Optimization ID ──────────────────────────────────────────────────────────
def generate_opt_id(asset: str, timeframe: str) -> str:
    fecha = date.today().strftime("%Y%m%d")
    return f"OPT-COMB002-{asset}-{timeframe}-PH3-{fecha}"


# ── Worker function ───────────────────────────────────────────────────────────
def run_exits_combo(args):
    scalp_coef, timescan, phase1_p, phase2a_p, phase2b_p, phase_a_rows, phase_b_rows, opt_id = args

    params = Comb002ImpulseParams(
        # Phase 1 locked — Signal
        stpmt_smooth_h=phase1_p["stpmt_smooth_h"],
        stpmt_smooth_b=phase1_p["stpmt_smooth_b"],
        stpmt_distance_max_h=phase1_p["stpmt_distance_max_h"],
        stpmt_distance_max_l=phase1_p["stpmt_distance_max_l"],
        # Phase 2a locked — Horaire
        horaire_allowed_hours_utc=phase2a_p["horaire_allowed_hours_utc"],
        # Phase 2b locked — Volatility
        volatility_atr_min=phase2b_p["volatility_atr_min"],
        volatility_atr_max=phase2b_p["volatility_atr_max"],
        # Phase 3: exits being tested
        scalping_target_coef_volat=scalp_coef,
        timescan_bars=timescan,
        # Stops at defaults
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        superstop_quality=2,
        superstop_coef_volat=3.0,
    )

    strategy = Comb002ImpulseStrategy(params)
    result_a = strategy.run(phase_a_rows)
    result_b = strategy.run(phase_b_rows)

    rob = (result_b.profit_factor / result_a.profit_factor
           if result_a.profit_factor > 0 else 0.0)

    return {
        "optimization_id":        opt_id,
        "scalping_target_coef":   scalp_coef,
        "timescan_bars":          timescan,
        "phase_a_pf":             round(result_a.profit_factor, 4),
        "phase_a_wr":             round(result_a.win_rate, 4),
        "phase_a_trades":         len(result_a.trades),
        "phase_a_equity":         round(result_a.equity_points, 2),
        "phase_b_pf":             round(result_b.profit_factor, 4),
        "phase_b_wr":             round(result_b.win_rate, 4),
        "phase_b_trades":         len(result_b.trades),
        "phase_b_equity":         round(result_b.equity_points, 2),
        "robustness":             round(rob, 4),
    }


def main():
    parser = argparse.ArgumentParser(
        description="COMB_002 IMPULSE Phase 3 — Exits Pool runner"
    )
    parser.add_argument("--asset",     required=True, choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True, choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument("--workers",   type=int, default=None)
    args = parser.parse_args()

    asset     = args.asset
    timeframe = args.timeframe
    workers   = args.workers or cpu_count()
    opt_id    = generate_opt_id(asset, timeframe)

    # Load locked params
    def load_json(fname):
        p = Path(fname)
        if not p.exists():
            print(f"[ERROR] {fname} not found.")
            sys.exit(1)
        with open(p) as fh:
            return json.load(fh)

    phase1_p  = load_json(f"COMB002_phase1_{asset}_{timeframe}_best_params.json")
    phase2a_p = load_json(f"COMB002_phase2a_{asset}_{timeframe}_best_params.json")
    phase2b_p = load_json(f"COMB002_phase2b_{asset}_{timeframe}_best_params.json")

    phase_a_file = f"{asset}_phase_A_{timeframe}.csv"
    phase_b_file = f"{asset}_phase_B_{timeframe}.csv"
    for f in [phase_a_file, phase_b_file]:
        if not Path(f).exists():
            print(f"[ERROR] {f} not found.")
            sys.exit(1)

    total = len(SCALPING_COEF_RANGE) * len(TIMESCAN_RANGE)

    print(f"\n{'='*80}")
    print(f"COMB_002 IMPULSE | Phase 3 Exits | {asset} {timeframe}")
    print(f"Optimization ID: {opt_id}")
    print(f"{'='*80}")
    print(f"Workers: {workers} | Grid: {len(SCALPING_COEF_RANGE)}×{len(TIMESCAN_RANGE)} = {total} combos")
    print(f"Phase 1 locked : smooth_h={phase1_p['stpmt_smooth_h']} smooth_b={phase1_p['stpmt_smooth_b']} "
          f"dh={phase1_p['stpmt_distance_max_h']} dl={phase1_p['stpmt_distance_max_l']}")
    print(f"Phase 2a locked: horaire={phase2a_p['horaire_label']}")
    print(f"Phase 2b locked: volatility={phase2b_p['volatility_label']} "
          f"({phase2b_p['volatility_atr_min']}-{phase2b_p['volatility_atr_max']})")

    phase_a_rows = load_ohlc_csv(phase_a_file)
    phase_b_rows = load_ohlc_csv(phase_b_file)
    print(f"Phase A: {len(phase_a_rows):,} bars | Phase B: {len(phase_b_rows):,} bars\n")

    all_combos = [
        (sc, ts, phase1_p, phase2a_p, phase2b_p, phase_a_rows, phase_b_rows, opt_id)
        for sc, ts in product(SCALPING_COEF_RANGE, TIMESCAN_RANGE)
    ]

    results = []
    completed = 0
    best_rob = 0.0
    best_row = None

    with Pool(processes=workers) as pool:
        for row in pool.imap_unordered(run_exits_combo, all_combos, chunksize=5):
            results.append(row)
            completed += 1
            if row["robustness"] > best_rob:
                best_rob = row["robustness"]
                best_row = row
                flag = ">>> PASS <<<" if best_rob >= ROBUSTNESS_THRESHOLD else ""
                print(f"  [{completed:>2}/{total}] NEW BEST {flag}: "
                      f"coef={row['scalping_target_coef']:.1f} ts={row['timescan_bars']} | "
                      f"Rob={best_rob:.4f} | "
                      f"PF_A={row['phase_a_pf']:.3f} PF_B={row['phase_b_pf']:.3f} | "
                      f"T_A={row['phase_a_trades']} T_B={row['phase_b_trades']}")
                sys.stdout.flush()

    results.sort(key=lambda x: x["robustness"], reverse=True)

    for r in results:
        r["asset"]     = asset
        r["timeframe"] = timeframe

    fields = ["optimization_id", "asset", "timeframe",
              "scalping_target_coef", "timescan_bars",
              "phase_a_pf", "phase_a_wr", "phase_a_trades", "phase_a_equity",
              "phase_b_pf", "phase_b_wr", "phase_b_trades", "phase_b_equity",
              "robustness"]

    log_file = f"COMB002_phase3_{asset}_{timeframe}_exits_log.csv"
    with open(log_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OK] {log_file}")

    best = results[0]
    best_params = {
        "optimization_id":           opt_id,
        "strategy":                  "COMB_002_IMPULSE",
        "asset":                     asset,
        "timeframe":                 timeframe,
        "phase":                     "3",
        # Phase 1 locked
        "stpmt_smooth_h":            phase1_p["stpmt_smooth_h"],
        "stpmt_smooth_b":            phase1_p["stpmt_smooth_b"],
        "stpmt_distance_max_h":      phase1_p["stpmt_distance_max_h"],
        "stpmt_distance_max_l":      phase1_p["stpmt_distance_max_l"],
        # Phase 2a locked
        "horaire_label":             phase2a_p["horaire_label"],
        "horaire_allowed_hours_utc": phase2a_p["horaire_allowed_hours_utc"],
        # Phase 2b locked
        "volatility_label":          phase2b_p["volatility_label"],
        "volatility_atr_min":        phase2b_p["volatility_atr_min"],
        "volatility_atr_max":        phase2b_p["volatility_atr_max"],
        # Phase 3 best
        "scalping_target_coef_volat": best["scalping_target_coef"],
        "timescan_bars":              best["timescan_bars"],
        "robustness":                 best["robustness"],
        "phase_a_pf":                 best["phase_a_pf"],
        "phase_b_pf":                 best["phase_b_pf"],
        "phase_a_trades":             best["phase_a_trades"],
        "phase_b_trades":             best["phase_b_trades"],
        "robustness_pass":            best["robustness"] >= ROBUSTNESS_THRESHOLD,
        "min_trades_pass":            best["phase_a_trades"] >= MIN_TRADES,
    }

    best_file = f"COMB002_phase3_{asset}_{timeframe}_best_params.json"
    with open(best_file, "w") as fh:
        json.dump(best_params, fh, indent=2)
    print(f"[OK] {best_file}")

    status = ">>> PASS <<<" if best["robustness"] >= ROBUSTNESS_THRESHOLD else "!!! FAIL !!!"
    print(f"\n{'='*80}")
    print(f"PHASE 3 DONE: {asset} {timeframe} [{status}]")
    print(f"  ID:                      {opt_id}")
    print(f"  scalping_target_coef   = {best['scalping_target_coef']}")
    print(f"  timescan_bars          = {best['timescan_bars']}")
    print(f"  robustness             = {best['robustness']:.4f}")
    print(f"  phase_a_pf             = {best['phase_a_pf']:.4f}")
    print(f"  phase_b_pf             = {best['phase_b_pf']:.4f}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
