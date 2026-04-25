"""
COMB_002_IMPULSE Phase 2a — Horaire Optimization (Pool Runner)
Optimiza el filtro horario con los params de Phase 1 bloqueados.

Metodología en 2 pasos:
  Paso 1: Baseline 24h + análisis por hora individual
  Paso 2: 12 perfiles predefinidos (incluye equivalentes Mogalef CET/CEST)

Nota timezone: Mogalef usa CET (París) = UTC+1 invierno / UTC+2 verano.
  - Ventana 1 Mogalef (9-17 CET) = 8-16 UTC invierno / 7-15 UTC verano
  - Ventana 2 Mogalef (20-22 CET) = 19-21 UTC invierno / 18-20 UTC verano
Nuestros datos están en UTC.

Uso:
  python3 phase2a_COMB002_horaire_pool_runner.py --asset ES --timeframe 5m
  python3 phase2a_COMB002_horaire_pool_runner.py --asset YM --timeframe 10m --workers 8
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

# ── 12 Horaire profiles (UTC) ─────────────────────────────────────────────────
HORAIRE_PROFILES = [
    {"id": 1,  "label": "24h_no_filter",         "hours": list(range(0, 24))},
    {"id": 2,  "label": "US_regular_9_15",        "hours": list(range(9, 16))},
    {"id": 3,  "label": "US_extended_9_17",       "hours": list(range(9, 18))},
    {"id": 4,  "label": "US_premarket_8_16",      "hours": list(range(8, 17))},
    {"id": 5,  "label": "NY_morning_9_12",        "hours": list(range(9, 13))},
    {"id": 6,  "label": "NY_afternoon_12_16",     "hours": list(range(12, 17))},
    {"id": 7,  "label": "Mogalef_V1_CET_8_16",   "hours": list(range(8, 17))},   # 9-17 CET invierno
    {"id": 8,  "label": "Mogalef_V1_CEST_7_15",  "hours": list(range(7, 16))},   # 9-17 CEST verano
    {"id": 9,  "label": "Mogalef_V2_CET_19_21",  "hours": [19, 20, 21]},          # 20-22 CET invierno
    {"id": 10, "label": "Mogalef_V2_CEST_18_20", "hours": [18, 19, 20]},          # 20-22 CEST verano
    {"id": 11, "label": "Mogalef_BOTH_CET",      "hours": list(range(8, 17)) + [19, 20, 21]},
    {"id": 12, "label": "Mogalef_BOTH_CEST",     "hours": list(range(7, 16)) + [18, 19, 20]},
]

# ── Worker function ───────────────────────────────────────────────────────────
def run_horaire_profile(args):
    profile, phase1_params, phase_a_rows, phase_b_rows = args

    params = Comb002ImpulseParams(
        # Phase 1 locked signal params
        stpmt_smooth_h=phase1_params["stpmt_smooth_h"],
        stpmt_smooth_b=phase1_params["stpmt_smooth_b"],
        stpmt_distance_max_h=phase1_params["stpmt_distance_max_h"],
        stpmt_distance_max_l=phase1_params["stpmt_distance_max_l"],
        # Phase 2a: horaire being tested
        horaire_allowed_hours_utc=profile["hours"],
        # All others at defaults
        volatility_atr_min=0.0,
        volatility_atr_max=500.0,
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
        "profile_id":    profile["id"],
        "label":         profile["label"],
        "hours_utc":     str(profile["hours"]),
        "phase_a_pf":    round(result_a.profit_factor, 4),
        "phase_a_wr":    round(result_a.win_rate, 4),
        "phase_a_trades": len(result_a.trades),
        "phase_a_equity": round(result_a.equity_points, 2),
        "phase_b_pf":    round(result_b.profit_factor, 4),
        "phase_b_wr":    round(result_b.win_rate, 4),
        "phase_b_trades": len(result_b.trades),
        "phase_b_equity": round(result_b.equity_points, 2),
        "robustness":    round(rob, 4),
    }


def main():
    parser = argparse.ArgumentParser(
        description="COMB_002 IMPULSE Phase 2a — Horaire Pool runner"
    )
    parser.add_argument("--asset",     required=True, choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True, choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()

    asset     = args.asset
    timeframe = args.timeframe
    workers   = args.workers or min(cpu_count(), len(HORAIRE_PROFILES))

    # Load Phase 1 best params
    phase1_file = f"COMB002_phase1_{asset}_{timeframe}_best_params.json"
    if not Path(phase1_file).exists():
        print(f"[ERROR] {phase1_file} not found. Run Phase 1 first.")
        sys.exit(1)
    with open(phase1_file) as fh:
        phase1_params = json.load(fh)

    phase_a_file = f"{asset}_phase_A_{timeframe}.csv"
    phase_b_file = f"{asset}_phase_B_{timeframe}.csv"
    for f in [phase_a_file, phase_b_file]:
        if not Path(f).exists():
            print(f"[ERROR] {f} not found.")
            sys.exit(1)

    print(f"\n{'='*80}")
    print(f"COMB_002 IMPULSE | Phase 2a Horaire | {asset} {timeframe}")
    print(f"{'='*80}")
    print(f"Workers: {workers} | Profiles: {len(HORAIRE_PROFILES)}")
    print(f"Phase 1 locked: smooth_h={phase1_params['stpmt_smooth_h']} "
          f"smooth_b={phase1_params['stpmt_smooth_b']} "
          f"dh={phase1_params['stpmt_distance_max_h']} "
          f"dl={phase1_params['stpmt_distance_max_l']}")

    phase_a_rows = load_ohlc_csv(phase_a_file)
    phase_b_rows = load_ohlc_csv(phase_b_file)
    print(f"Phase A: {len(phase_a_rows):,} bars | Phase B: {len(phase_b_rows):,} bars\n")

    combos = [(p, phase1_params, phase_a_rows, phase_b_rows) for p in HORAIRE_PROFILES]

    results = []
    with Pool(processes=workers) as pool:
        for row in pool.imap_unordered(run_horaire_profile, combos, chunksize=1):
            results.append(row)
            flag = ">>> PASS <<<" if row["robustness"] >= ROBUSTNESS_THRESHOLD else ""
            print(f"  [{row['profile_id']:>2}] {row['label']:<30} "
                  f"Rob={row['robustness']:.4f} {flag} | "
                  f"PF_A={row['phase_a_pf']:.3f} PF_B={row['phase_b_pf']:.3f} | "
                  f"T_A={row['phase_a_trades']} T_B={row['phase_b_trades']}")
            sys.stdout.flush()

    # Sort by robustness
    results.sort(key=lambda x: x["robustness"], reverse=True)

    # Add metadata
    for r in results:
        r["asset"]     = asset
        r["timeframe"] = timeframe

    fields = ["asset", "timeframe", "profile_id", "label", "hours_utc",
              "phase_a_pf", "phase_a_wr", "phase_a_trades", "phase_a_equity",
              "phase_b_pf", "phase_b_wr", "phase_b_trades", "phase_b_equity",
              "robustness"]

    log_file = f"COMB002_phase2a_{asset}_{timeframe}_horaire_log.csv"
    with open(log_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OK] {log_file}")

    # Best result
    best = results[0]
    no_filter = next(r for r in results if r["profile_id"] == 1)

    # Mogalef comparison
    mogalef_ids = [7, 8, 9, 10, 11, 12]
    mogalef_results = [r for r in results if r["profile_id"] in mogalef_ids]
    best_mogalef = max(mogalef_results, key=lambda x: x["robustness"])

    comparison = {
        "winner_empirical":  best["label"],
        "winner_rob":        best["robustness"],
        "best_mogalef":      best_mogalef["label"],
        "best_mogalef_rob":  best_mogalef["robustness"],
        "coincide":          best["profile_id"] in mogalef_ids,
        "baseline_24h_rob":  no_filter["robustness"],
        "improvement_vs_24h": round(best["robustness"] - no_filter["robustness"], 4),
    }

    # Save best params
    best_params = {
        "strategy":              "COMB_002_IMPULSE",
        "asset":                 asset,
        "timeframe":             timeframe,
        "phase":                 "2a",
        "stpmt_smooth_h":        phase1_params["stpmt_smooth_h"],
        "stpmt_smooth_b":        phase1_params["stpmt_smooth_b"],
        "stpmt_distance_max_h":  phase1_params["stpmt_distance_max_h"],
        "stpmt_distance_max_l":  phase1_params["stpmt_distance_max_l"],
        "horaire_profile_id":    best["profile_id"],
        "horaire_label":         best["label"],
        "horaire_allowed_hours_utc": HORAIRE_PROFILES[best["profile_id"] - 1]["hours"],
        "robustness":            best["robustness"],
        "phase_a_pf":            best["phase_a_pf"],
        "phase_b_pf":            best["phase_b_pf"],
        "phase_a_trades":        best["phase_a_trades"],
        "phase_b_trades":        best["phase_b_trades"],
        "robustness_pass":       best["robustness"] >= ROBUSTNESS_THRESHOLD,
        "min_trades_pass":       best["phase_a_trades"] >= MIN_TRADES,
        "mogalef_comparison":    comparison,
    }

    best_file = f"COMB002_phase2a_{asset}_{timeframe}_best_params.json"
    with open(best_file, "w") as fh:
        json.dump(best_params, fh, indent=2)
    print(f"[OK] {best_file}")

    print(f"\n{'='*80}")
    print(f"PHASE 2a DONE: {asset} {timeframe}")
    print(f"  Winner:         {best['label']}")
    print(f"  Robustness:     {best['robustness']:.4f}")
    print(f"  PF_A / PF_B:    {best['phase_a_pf']:.4f} / {best['phase_b_pf']:.4f}")
    print(f"  Baseline 24h:   Rob={no_filter['robustness']:.4f}")
    print(f"  Mejora vs 24h:  {comparison['improvement_vs_24h']:+.4f}")
    print(f"  Best Mogalef:   {best_mogalef['label']} Rob={best_mogalef['robustness']:.4f}")
    print(f"  Coincide:       {'SI ✓' if comparison['coincide'] else 'NO — datos mandan'}")
    print(f"{'='*80}\n")

    try:
        repo_root = Path(__file__).resolve().parents[1]
        opt_id = f"OPT-COMB002-{asset}-{timeframe}-PH2a-{__import__('datetime').date.today().strftime('%Y%m%d')}"
        subprocess.run(["git", "add", f"mgf-control/{best_file}"],
            cwd=repo_root, check=True)
        msg = (f"PH2a DONE - {asset} {timeframe} | {opt_id} | "
               f"Rob={best['robustness']:.4f} {'PASS' if best['robustness'] >= ROBUSTNESS_THRESHOLD else 'FAIL'} | "
               f"Horaire={best['label']}")
        subprocess.run(["git", "commit", "-m", msg], cwd=repo_root, check=True)
        subprocess.run(["git", "push"], cwd=repo_root, check=True)
        print(f"[GIT] Pushed: {msg}")
    except subprocess.CalledProcessError as e:
        print(f"[GIT WARNING] Push failed: {e} — results saved locally")


if __name__ == "__main__":
    main()
