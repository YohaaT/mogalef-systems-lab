"""Phase 1 Optimization (5m): Signal (STPMT_DIV) — Block Runner

Tests 625 combinations of STPMT signal parameters.
Split:
  Block 1 (TANK) : combos[0:175]   = smooth_h=[1] (125) + smooth_h=2 smooth_b=[1,2] (50)
  Block 2 (VPS)  : combos[175:625] = smooth_h=2 smooth_b=[3,4,5] (75) + smooth_h=[3,4,5] (375)

Locked from methodology:
  Contexto/Exits/Stops at defaults (Phase 1 tests signal only)
  horaire=[12..15] UTC, volatility=(0,500), trend defaults
"""

import csv
import json
import sys
from multiprocessing import Pool
from pathlib import Path

from COMB_001_TREND_V1_vectorized import (
    Comb001TrendParams,
    Comb001TrendVectorized,
    load_ohlc_csv,
)

# ── Block assignment ──────────────────────────────────────────────────────────
BLOCK_NUM = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# Full grid (625 combos, same order as Phase 1 original)
SMOOTH_H_VALS  = [1, 2, 3, 4, 5]
SMOOTH_B_VALS  = [1, 2, 3, 4, 5]
DIST_H_VALS    = [25, 50, 75, 100, 125]
DIST_L_VALS    = [25, 50, 75, 100, 125]

def build_all_combos():
    combos = []
    for sh in SMOOTH_H_VALS:
        for sb in SMOOTH_B_VALS:
            for dh in DIST_H_VALS:
                for dl in DIST_L_VALS:
                    combos.append((sh, sb, dh, dl))
    return combos  # 625 combos, indices 0-624

ALL_COMBOS = build_all_combos()

# Block slices:  Block1=TANK [0:175],  Block2=VPS [175:625]
BLOCK_SLICES = {1: (0, 175), 2: (175, 625)}
BLOCK_NAMES  = {1: "TANK", 2: "VPS_BO"}

start_idx, end_idx = BLOCK_SLICES[BLOCK_NUM]
BLOCK_COMBOS = ALL_COMBOS[start_idx:end_idx]

# ── Defaults (everything except signal) ──────────────────────────────────────
CONTEXT_DEFAULTS = {
    "trend_r1": 1,
    "trend_r2": 90,
    "trend_r3": 150,
    "horaire_allowed_hours_utc": list(range(12, 16)),  # 12-15 UTC default
    "contexto_blocked_weekdays": [],
    "volatility_atr_min": 0.0,
    "volatility_atr_max": 500.0,
}
EXIT_DEFAULTS = {
    "target_atr_multiplier": 10.0,
    "timescan_bars": 30,
}
STOP_DEFAULTS = {
    "stop_intelligent_quality": 2,
    "stop_intelligent_recent_volat": 2,
    "stop_intelligent_ref_volat": 20,
    "stop_intelligent_coef_volat": 5.0,
}


def _worker(args):
    rows_a, rows_b, smooth_h, smooth_b, dist_h, dist_l = args

    params = Comb001TrendParams(
        stpmt_smooth_h=smooth_h,
        stpmt_smooth_b=smooth_b,
        stpmt_distance_max_h=dist_h,
        stpmt_distance_max_l=dist_l,
        **CONTEXT_DEFAULTS,
        **EXIT_DEFAULTS,
        **STOP_DEFAULTS,
    )

    strat = Comb001TrendVectorized(params)
    res_a = strat.run(rows_a)
    res_b = strat.run(rows_b)

    robustness = (res_b.profit_factor / res_a.profit_factor
                  if res_a.profit_factor > 0 else 0.0)

    return {
        "smooth_h": smooth_h,
        "smooth_b": smooth_b,
        "dist_h": dist_h,
        "dist_l": dist_l,
        "phase_a_pf":     round(res_a.profit_factor, 4),
        "phase_a_wr":     round(res_a.win_rate, 4),
        "phase_a_trades": len(res_a.trades),
        "phase_a_equity": round(res_a.equity_points, 2),
        "phase_b_pf":     round(res_b.profit_factor, 4),
        "phase_b_wr":     round(res_b.win_rate, 4),
        "phase_b_trades": len(res_b.trades),
        "phase_b_equity": round(res_b.equity_points, 2),
        "robustness":     round(robustness, 4),
    }


def run_block(block_num, rows_a, rows_b):
    server = BLOCK_NAMES[block_num]
    n_combos = len(BLOCK_COMBOS)

    print(f"\n{'='*80}")
    print(f"PHASE 1 (5m) — BLOCK {block_num} [{server}]  combos {start_idx+1}-{end_idx}")
    print(f"{'='*80}")
    print(f"Signal grid: smooth_h, smooth_b, dist_h, dist_l")
    print(f"Total combos this block: {n_combos}\n")

    args_list = [
        (rows_a, rows_b, sh, sb, dh, dl)
        for (sh, sb, dh, dl) in BLOCK_COMBOS
    ]

    num_workers = 8
    with Pool(processes=num_workers) as pool:
        results = pool.map(_worker, args_list)

    results.sort(key=lambda x: x["robustness"], reverse=True)

    # CSV log
    log_file = f"phase1_5m_signal_block_{block_num}_log.csv"
    with open(log_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"[OK] {log_file}")

    # Best params JSON
    best = results[0]
    best_file = f"phase1_5m_signal_block_{block_num}_best_params.json"
    best_dict = {
        "block": block_num,
        "server": server,
        "smooth_h": best["smooth_h"],
        "smooth_b": best["smooth_b"],
        "dist_h":   best["dist_h"],
        "dist_l":   best["dist_l"],
        "robustness": best["robustness"],
        "phase_a_pf": best["phase_a_pf"],
        "phase_b_pf": best["phase_b_pf"],
    }
    with open(best_file, "w") as f:
        json.dump(best_dict, f, indent=2)
    print(f"[OK] {best_file}")

    # Top 10
    top10_file = f"phase1_5m_signal_block_{block_num}_top10.csv"
    with open(top10_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results[:10])
    print(f"[OK] {top10_file}")

    print(f"\n[BEST] smooth_h={best['smooth_h']}, smooth_b={best['smooth_b']}, "
          f"dist_h={best['dist_h']}, dist_l={best['dist_l']}")
    print(f"       Phase_A PF={best['phase_a_pf']:.4f}  "
          f"Phase_B PF={best['phase_b_pf']:.4f}  "
          f"Robustness={best['robustness']:.4f}")


def main():
    print("Loading 5m data...")
    rows_a = load_ohlc_csv("YM_phase_A_5m.csv")
    rows_b = load_ohlc_csv("YM_phase_B_5m.csv")
    print(f"Phase A: {len(rows_a)} bars (5m)")
    print(f"Phase B: {len(rows_b)} bars (5m)")

    run_block(BLOCK_NUM, rows_a, rows_b)


if __name__ == "__main__":
    main()
