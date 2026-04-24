"""Phase 4 (5m): Stop Intelligent Optimization

Tests 108 combinations of Stop Intelligent parameters.
Can be split across 2 servers (Block 1 + Block 2) or run as single block.

Locked from Phase 1 + 2 + 3:
  - Best STPMT signal (Phase 1)
  - Best Contexto (Phase 2)
  - Best Exits (Phase 3)

Grid (108 combos):
  Block 1 (48):  quality=[1,2] × recent=[1,2,3] × ref_vol=[10,20] × coef=[3.0,5.0]
  Block 2 (60):  quality=[3] × recent=[1,2,3] × ref_vol=[10,20,30] × coef=[5.0,7.0]

Usage:
  Single server: python phase4_5m_stops_optimizer.py
  Split across servers: python phase4_5m_stops_optimizer.py 1  (TANK Block 1)
                        python phase4_5m_stops_optimizer.py 2  (VPS Block 2)
"""

import csv
import json
import sys
from multiprocessing import Pool
from COMB_001_TREND_V1_vectorized import Comb001TrendParams, Comb001TrendVectorized, load_ohlc_csv

# Load Phase 1 + 2 + 3
with open("phase1_5m_best_params.json") as f:
    phase1 = json.load(f)
with open("phase2_5m_best_params.json") as f:
    phase2 = json.load(f)
with open("phase3_5m_exits_best_params.json") as f:
    phase3 = json.load(f)

SIGNAL_BEST = phase1["signal_best"]
CONTEXTO_BEST = phase2["contexto_component"]
EXITS_BEST = phase3

# Determine block (if running split across servers)
BLOCK_NUM = int(sys.argv[1]) if len(sys.argv) > 1 else 0  # 0=single, 1=TANK, 2=VPS

# Stop Intelligent grid (split into 2 blocks for parallelism)
if BLOCK_NUM == 1 or BLOCK_NUM == 0:
    QUALITY_VALUES = [1, 2]
    RECENT_VALUES = [1, 2, 3]
    REF_VALUES = [10, 20]
    COEF_VALUES = [3.0, 5.0]

if BLOCK_NUM == 2:
    QUALITY_VALUES = [3]
    RECENT_VALUES = [1, 2, 3]
    REF_VALUES = [10, 20, 30]
    COEF_VALUES = [5.0, 7.0]

if BLOCK_NUM == 0:  # Single run: combine both blocks
    QUALITY_VALUES = [1, 2, 3]
    RECENT_VALUES = [1, 2, 3]
    REF_VALUES = [10, 20, 30]
    COEF_VALUES = [3.0, 5.0, 7.0]


def _worker(args):
    rows_a, rows_b, quality, recent, ref_vol, coef = args

    params = Comb001TrendParams(
        stpmt_smooth_h=SIGNAL_BEST["stpmt_smooth_h"],
        stpmt_smooth_b=SIGNAL_BEST["stpmt_smooth_b"],
        stpmt_distance_max_h=SIGNAL_BEST["stpmt_distance_max_h"],
        stpmt_distance_max_l=SIGNAL_BEST["stpmt_distance_max_l"],
        trend_r1=CONTEXTO_BEST["trend_filter"]["trend_r1"],
        trend_r2=CONTEXTO_BEST["trend_filter"]["trend_r2"],
        trend_r3=CONTEXTO_BEST["trend_filter"]["trend_r3"],
        horaire_allowed_hours_utc=CONTEXTO_BEST["horaire"]["hours"],
        contexto_blocked_weekdays=CONTEXTO_BEST["weekday_filter"]["blocked_days"],
        volatility_atr_min=CONTEXTO_BEST["volatility"]["atr_min"],
        volatility_atr_max=CONTEXTO_BEST["volatility"]["atr_max"],
        target_atr_multiplier=EXITS_BEST["target_atr_multiplier"],
        timescan_bars=EXITS_BEST["timescan_bars"],
        stop_intelligent_quality=quality,
        stop_intelligent_recent_volat=recent,
        stop_intelligent_ref_volat=ref_vol,
        stop_intelligent_coef_volat=coef,
    )

    strat = Comb001TrendVectorized(params)
    res_a = strat.run(rows_a)
    res_b = strat.run(rows_b)

    robustness = res_b.profit_factor / res_a.profit_factor if res_a.profit_factor > 0 else 0.0

    return {
        "quality": quality,
        "recent": recent,
        "ref_vol": ref_vol,
        "coef": coef,
        "phase_a_pf": round(res_a.profit_factor, 4),
        "phase_a_wr": round(res_a.win_rate, 4),
        "phase_a_trades": len(res_a.trades),
        "phase_a_equity": round(res_a.equity_points, 2),
        "phase_b_pf": round(res_b.profit_factor, 4),
        "phase_b_wr": round(res_b.win_rate, 4),
        "phase_b_trades": len(res_b.trades),
        "phase_b_equity": round(res_b.equity_points, 2),
        "robustness": round(robustness, 4),
    }


def main():
    print("\nLoading 5m data...")
    rows_a = load_ohlc_csv("YM_phase_A_5m.csv")
    rows_b = load_ohlc_csv("YM_phase_B_5m.csv")

    block_label = {0: "SINGLE", 1: "BLOCK 1 (TANK)", 2: "BLOCK 2 (VPS)"}.get(BLOCK_NUM, "?")
    print("\n" + "="*80)
    print(f"PHASE 4 (5m) - STOP INTELLIGENT OPTIMIZATION — {block_label}")
    print("="*80)
    print(f"Grid: quality={QUALITY_VALUES} x recent={RECENT_VALUES} x ref_vol={REF_VALUES} x coef={COEF_VALUES}")
    n_combos = len(QUALITY_VALUES) * len(RECENT_VALUES) * len(REF_VALUES) * len(COEF_VALUES)
    print(f"Total combos: {n_combos}\n")

    args_list = [
        (rows_a, rows_b, q, r, rf, c)
        for q in QUALITY_VALUES
        for r in RECENT_VALUES
        for rf in REF_VALUES
        for c in COEF_VALUES
    ]

    with Pool(processes=8) as pool:
        results = pool.map(_worker, args_list)

    results.sort(key=lambda x: x["robustness"], reverse=True)

    # CSV log
    block_suffix = f"_block_{BLOCK_NUM}" if BLOCK_NUM > 0 else ""
    log_file = f"phase4_5m_stops{block_suffix}_log.csv"
    with open(log_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"[OK] {log_file}")

    # Best JSON
    best = results[0]
    best_file = f"phase4_5m_stops{block_suffix}_best_params.json"
    with open(best_file, "w") as f:
        json.dump({
            "block": BLOCK_NUM if BLOCK_NUM > 0 else "single",
            "quality": best["quality"],
            "recent": best["recent"],
            "ref_vol": best["ref_vol"],
            "coef": best["coef"],
            "robustness": best["robustness"],
            "phase_a_pf": best["phase_a_pf"],
            "phase_b_pf": best["phase_b_pf"],
        }, f, indent=2)
    print(f"[OK] {best_file}")

    # Top 5
    with open(f"phase4_5m_stops{block_suffix}_top5.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results[:5])

    print(f"\n[BEST] quality={best['quality']}, recent={best['recent']}, "
          f"ref_vol={best['ref_vol']}, coef={best['coef']:.1f}")
    print(f"       Robustness={best['robustness']:.4f}  A_PF={best['phase_a_pf']:.4f}  B_PF={best['phase_b_pf']:.4f}")


if __name__ == "__main__":
    main()
