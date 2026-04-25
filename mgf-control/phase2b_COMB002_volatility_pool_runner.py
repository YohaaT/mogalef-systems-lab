"""
COMB_002_IMPULSE Phase 2b — Volatility Filter Optimization (Pool Runner)
Optimiza los bounds de ATR con Signal (Ph1) + Horaire (Ph2a) bloqueados.

5 perfiles de volatilidad (ATR bounds):
  1. (0, 500)   — sin filtro (baseline)
  2. (10, 500)  — piso mínimo (elimina volatilidad muy baja)
  3. (0, 200)   — techo máximo (elimina volatilidad extrema)
  4. (10, 250)  — banda ajustada
  5. (20, 200)  — banda selectiva (solo mercado "normal")

Uso:
  python3 phase2b_COMB002_volatility_pool_runner.py --asset ES --timeframe 5m
  python3 phase2b_COMB002_volatility_pool_runner.py --asset YM --timeframe 10m --workers 8
"""

import argparse
import csv
import json
import subprocess
import sys
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

VOLATILITY_PROFILES = [
    {"id": 1, "label": "no_filter_0_500",     "atr_min": 0.0,  "atr_max": 500.0},
    {"id": 2, "label": "min_floor_10_500",    "atr_min": 10.0, "atr_max": 500.0},
    {"id": 3, "label": "max_ceiling_0_200",   "atr_min": 0.0,  "atr_max": 200.0},
    {"id": 4, "label": "tight_band_10_250",   "atr_min": 10.0, "atr_max": 250.0},
    {"id": 5, "label": "selective_20_200",    "atr_min": 20.0, "atr_max": 200.0},
]


def run_volatility_profile(args):
    profile, phase1_params, phase2a_params, phase_a_rows, phase_b_rows = args

    params = Comb002ImpulseParams(
        # Phase 1 locked
        stpmt_smooth_h=phase1_params["stpmt_smooth_h"],
        stpmt_smooth_b=phase1_params["stpmt_smooth_b"],
        stpmt_distance_max_h=phase1_params["stpmt_distance_max_h"],
        stpmt_distance_max_l=phase1_params["stpmt_distance_max_l"],
        # Phase 2a locked
        horaire_allowed_hours_utc=phase2a_params["horaire_allowed_hours_utc"],
        # Phase 2b: volatility being tested
        volatility_atr_min=profile["atr_min"],
        volatility_atr_max=profile["atr_max"],
        # Defaults
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        scalping_target_coef_volat=3.0,
        timescan_bars=15,
        superstop_quality=2,
        superstop_coef_volat=3.0,
    )

    strategy = Comb002ImpulseStrategy(params)
    result_a = strategy.run(phase_a_rows)
    result_b = strategy.run(phase_b_rows)

    rob = (result_b.profit_factor / result_a.profit_factor
           if result_a.profit_factor > 0 else 0.0)

    return {
        "profile_id":     profile["id"],
        "label":          profile["label"],
        "atr_min":        profile["atr_min"],
        "atr_max":        profile["atr_max"],
        "phase_a_pf":     round(result_a.profit_factor, 4),
        "phase_a_wr":     round(result_a.win_rate, 4),
        "phase_a_trades": len(result_a.trades),
        "phase_a_equity": round(result_a.equity_points, 2),
        "phase_b_pf":     round(result_b.profit_factor, 4),
        "phase_b_wr":     round(result_b.win_rate, 4),
        "phase_b_trades": len(result_b.trades),
        "phase_b_equity": round(result_b.equity_points, 2),
        "robustness":     round(rob, 4),
    }


def main():
    parser = argparse.ArgumentParser(
        description="COMB_002 IMPULSE Phase 2b — Volatility Pool runner"
    )
    parser.add_argument("--asset",     required=True, choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True, choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()

    asset     = args.asset
    timeframe = args.timeframe
    workers   = args.workers or min(cpu_count(), len(VOLATILITY_PROFILES))

    # Load Phase 1 best params
    phase1_file = f"COMB002_phase1_{asset}_{timeframe}_best_params.json"
    if not Path(phase1_file).exists():
        print(f"[ERROR] {phase1_file} not found.")
        sys.exit(1)
    with open(phase1_file) as fh:
        phase1_params = json.load(fh)

    # Load Phase 2a best params
    phase2a_file = f"COMB002_phase2a_{asset}_{timeframe}_best_params.json"
    if not Path(phase2a_file).exists():
        print(f"[ERROR] {phase2a_file} not found. Run Phase 2a first.")
        sys.exit(1)
    with open(phase2a_file) as fh:
        phase2a_params = json.load(fh)

    phase_a_file = f"{asset}_phase_A_{timeframe}.csv"
    phase_b_file = f"{asset}_phase_B_{timeframe}.csv"
    for f in [phase_a_file, phase_b_file]:
        if not Path(f).exists():
            print(f"[ERROR] {f} not found.")
            sys.exit(1)

    print(f"\n{'='*80}")
    print(f"COMB_002 IMPULSE | Phase 2b Volatility | {asset} {timeframe}")
    print(f"{'='*80}")
    print(f"Workers: {workers} | Profiles: {len(VOLATILITY_PROFILES)}")
    print(f"Phase 1 locked: smooth_h={phase1_params['stpmt_smooth_h']} "
          f"smooth_b={phase1_params['stpmt_smooth_b']} "
          f"dh={phase1_params['stpmt_distance_max_h']} "
          f"dl={phase1_params['stpmt_distance_max_l']}")
    print(f"Phase 2a locked: horaire={phase2a_params['horaire_label']} "
          f"({phase2a_params['horaire_allowed_hours_utc']})")

    phase_a_rows = load_ohlc_csv(phase_a_file)
    phase_b_rows = load_ohlc_csv(phase_b_file)
    print(f"Phase A: {len(phase_a_rows):,} bars | Phase B: {len(phase_b_rows):,} bars\n")

    combos = [(p, phase1_params, phase2a_params, phase_a_rows, phase_b_rows)
              for p in VOLATILITY_PROFILES]

    results = []
    with Pool(processes=workers) as pool:
        for row in pool.imap_unordered(run_volatility_profile, combos, chunksize=1):
            results.append(row)
            flag = ">>> PASS <<<" if row["robustness"] >= ROBUSTNESS_THRESHOLD else ""
            print(f"  [{row['profile_id']}] {row['label']:<25} "
                  f"Rob={row['robustness']:.4f} {flag} | "
                  f"PF_A={row['phase_a_pf']:.3f} PF_B={row['phase_b_pf']:.3f} | "
                  f"T_A={row['phase_a_trades']} T_B={row['phase_b_trades']}")
            sys.stdout.flush()

    results.sort(key=lambda x: x["robustness"], reverse=True)

    for r in results:
        r["asset"]     = asset
        r["timeframe"] = timeframe

    fields = ["asset", "timeframe", "profile_id", "label", "atr_min", "atr_max",
              "phase_a_pf", "phase_a_wr", "phase_a_trades", "phase_a_equity",
              "phase_b_pf", "phase_b_wr", "phase_b_trades", "phase_b_equity",
              "robustness"]

    log_file = f"COMB002_phase2b_{asset}_{timeframe}_volatility_log.csv"
    with open(log_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OK] {log_file}")

    best     = results[0]
    baseline = next(r for r in results if r["profile_id"] == 1)

    best_params = {
        "strategy":              "COMB_002_IMPULSE",
        "asset":                 asset,
        "timeframe":             timeframe,
        "phase":                 "2b",
        # Phase 1 locked
        "stpmt_smooth_h":        phase1_params["stpmt_smooth_h"],
        "stpmt_smooth_b":        phase1_params["stpmt_smooth_b"],
        "stpmt_distance_max_h":  phase1_params["stpmt_distance_max_h"],
        "stpmt_distance_max_l":  phase1_params["stpmt_distance_max_l"],
        # Phase 2a locked
        "horaire_label":         phase2a_params["horaire_label"],
        "horaire_allowed_hours_utc": phase2a_params["horaire_allowed_hours_utc"],
        # Phase 2b best
        "volatility_profile_id": best["profile_id"],
        "volatility_label":      best["label"],
        "volatility_atr_min":    best["atr_min"],
        "volatility_atr_max":    best["atr_max"],
        "robustness":            best["robustness"],
        "phase_a_pf":            best["phase_a_pf"],
        "phase_b_pf":            best["phase_b_pf"],
        "phase_a_trades":        best["phase_a_trades"],
        "phase_b_trades":        best["phase_b_trades"],
        "robustness_pass":       best["robustness"] >= ROBUSTNESS_THRESHOLD,
        "min_trades_pass":       best["phase_a_trades"] >= MIN_TRADES,
        "improvement_vs_baseline": round(best["robustness"] - baseline["robustness"], 4),
    }

    best_file = f"COMB002_phase2b_{asset}_{timeframe}_best_params.json"
    with open(best_file, "w") as fh:
        json.dump(best_params, fh, indent=2)
    print(f"[OK] {best_file}")

    print(f"\n{'='*80}")
    print(f"PHASE 2b DONE: {asset} {timeframe}")
    print(f"  Winner volatility:  {best['label']} ({best['atr_min']}-{best['atr_max']})")
    print(f"  Robustness:         {best['robustness']:.4f}")
    print(f"  PF_A / PF_B:        {best['phase_a_pf']:.4f} / {best['phase_b_pf']:.4f}")
    print(f"  Baseline (no filt): Rob={baseline['robustness']:.4f}")
    print(f"  Mejora vs baseline: {best_params['improvement_vs_baseline']:+.4f}")
    print(f"{'='*80}\n")

    try:
        repo_root = Path(__file__).resolve().parents[1]
        opt_id = f"OPT-COMB002-{asset}-{timeframe}-PH2b-{__import__('datetime').date.today().strftime('%Y%m%d')}"
        subprocess.run(["git", "add", f"mgf-control/{best_file}"],
            cwd=repo_root, check=True)
        msg = (f"PH2b DONE - {asset} {timeframe} | {opt_id} | "
               f"Rob={best['robustness']:.4f} {'PASS' if best['robustness'] >= ROBUSTNESS_THRESHOLD else 'FAIL'} | "
               f"Volat={best['label']}")
        subprocess.run(["git", "commit", "-m", msg], cwd=repo_root, check=True)
        subprocess.run(["git", "push"], cwd=repo_root, check=True)
        print(f"[GIT] Pushed: {msg}")
    except subprocess.CalledProcessError as e:
        print(f"[GIT WARNING] Push failed: {e} — results saved locally")


if __name__ == "__main__":
    main()
