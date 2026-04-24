"""
COMB_002_IMPULSE Phase 1 - Multi-Asset Signal Optimizer
Runs 5 blocks x 125 combos = 625 total per asset/timeframe.

Blocks partition by smooth_h value:
  Block 1: smooth_h=1 (125 combos: smooth_b × dist_h × dist_l = 5×5×5)
  Block 2: smooth_h=2 (125 combos)
  Block 3: smooth_h=3 (125 combos)
  Block 4: smooth_h=4 (125 combos)
  Block 5: smooth_h=5 (125 combos)

IMPULSE differs from TREND:
  - NO Trend Filter (catches impulses in all market regimes)
  - NO Volatility filter (kills IMPULSE performance per Mogalef)
  - TimeStop = 15 bars (shorter than Trend's 30)
  - SuperStop instead of Stop Inteligente

Usage:
  python phase1_COMB002_multiasset_runner.py --asset ES --timeframe 5m
  python phase1_COMB002_multiasset_runner.py --asset MNQ --timeframe 5m --block 3
  python phase1_COMB002_multiasset_runner.py --asset FDAX --timeframe 5m --block 1

Outputs (per asset/timeframe):
  COMB002_phase1_{ASSET}_{TF}_block_{N}_log.csv
  COMB002_phase1_{ASSET}_{TF}_block_{N}_top10.csv
  COMB002_phase1_{ASSET}_{TF}_block_{N}_best_params.json
  COMB002_phase1_{ASSET}_{TF}_full_log.csv          (all 5 blocks, only when running all)
  COMB002_phase1_{ASSET}_{TF}_top10.csv             (all 5 blocks, only when running all)
  COMB002_phase1_{ASSET}_{TF}_best_params.json      (final best, only when running all)
"""

import argparse
import csv
import json
import sys
from pathlib import Path

# ── Ensure COMB_002_IMPULSE_V1 can find its dependencies ──────────────────────
_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from COMB_002_IMPULSE_V1 import Comb002ImpulseStrategy, Comb002ImpulseParams, load_ohlc_csv

# ── Parameter grids (COMB_002_IMPULSE_PHASE_CONFIG.json Phase 1) ──────────────
SMOOTH_H_RANGE  = [1, 2, 3, 4, 5]         # Partitioned into 5 blocks
SMOOTH_B_RANGE  = [1, 2, 3, 4, 5]
DISTANCE_H_RANGE = [25, 75, 125, 175, 200]
DISTANCE_L_RANGE = [25, 75, 125, 175, 200]

SUPPORTED_ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
SUPPORTED_TIMEFRAMES = ["5m", "10m", "15m"]

# Robustness threshold (Mogalef methodology)
ROBUSTNESS_THRESHOLD = 0.80
MIN_TRADES_PHASE_A   = 20


def get_data_filenames(asset: str, timeframe: str):
    """Return (phase_a_csv, phase_b_csv) for asset/timeframe."""
    phase_a = f"{asset}_phase_A_{timeframe}.csv"
    phase_b = f"{asset}_phase_B_{timeframe}.csv"
    return phase_a, phase_b


def run_block(block_num: int, smooth_h_values: list,
              phase_a_rows: list, phase_b_rows: list,
              asset: str, timeframe: str):
    """Optimize all 125 combos for a given smooth_h block."""

    print(f"\n{'='*80}")
    print(f"COMB_002 IMPULSE | Phase 1 Signal | {asset} {timeframe} | Block {block_num}/5")
    print(f"{'='*80}")
    print(f"smooth_h values in block: {smooth_h_values}")

    results      = []
    best_robustness = 0.0
    best_params     = None
    combo_num       = 0
    total_combos    = (len(smooth_h_values) * len(SMOOTH_B_RANGE) *
                       len(DISTANCE_H_RANGE) * len(DISTANCE_L_RANGE))
    print(f"Total combos: {total_combos}\n")

    for smooth_h in smooth_h_values:
        for smooth_b in SMOOTH_B_RANGE:
            for dist_h in DISTANCE_H_RANGE:
                for dist_l in DISTANCE_L_RANGE:
                    combo_num += 1

                    params = Comb002ImpulseParams(
                        # ── PHASE 1: Signal params (VARIED) ──
                        stpmt_smooth_h=smooth_h,
                        stpmt_smooth_b=smooth_b,
                        stpmt_distance_max_h=dist_h,
                        stpmt_distance_max_l=dist_l,
                        # ── All other components at Mogalef defaults ──
                        horaire_allowed_hours_utc=list(range(9, 16)),
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

                    # Run Phase A (train) + Phase B (unseen validation)
                    strategy = Comb002ImpulseStrategy(params)
                    result_a = strategy.run(phase_a_rows)
                    result_b = strategy.run(phase_b_rows)

                    # Robustness = Phase_B_PF / Phase_A_PF
                    if result_a.profit_factor > 0:
                        robustness = result_b.profit_factor / result_a.profit_factor
                    else:
                        robustness = 0.0

                    row = {
                        "asset":         asset,
                        "timeframe":     timeframe,
                        "block":         block_num,
                        "combo":         combo_num,
                        "smooth_h":      smooth_h,
                        "smooth_b":      smooth_b,
                        "dist_max_h":    dist_h,
                        "dist_max_l":    dist_l,
                        "phase_a_pf":    round(result_a.profit_factor, 4),
                        "phase_a_wr":    round(result_a.win_rate, 4),
                        "phase_a_trades": len(result_a.trades),
                        "phase_a_equity": round(result_a.equity_points, 2),
                        "phase_b_pf":    round(result_b.profit_factor, 4),
                        "phase_b_wr":    round(result_b.win_rate, 4),
                        "phase_b_trades": len(result_b.trades),
                        "phase_b_equity": round(result_b.equity_points, 2),
                        "robustness":    round(robustness, 4),
                    }
                    results.append(row)

                    if robustness > best_robustness:
                        best_robustness = robustness
                        best_params     = params
                        flag = ">>> PASS <<<" if robustness >= ROBUSTNESS_THRESHOLD else ""
                        print(
                            f"  [{combo_num:>3}/{total_combos}] NEW BEST {flag}: "
                            f"h={smooth_h} b={smooth_b} dh={dist_h} dl={dist_l} | "
                            f"Rob={robustness:.4f} | "
                            f"PF_A={result_a.profit_factor:.3f} "
                            f"PF_B={result_b.profit_factor:.3f} | "
                            f"T_A={len(result_a.trades)} T_B={len(result_b.trades)}"
                        )

                    if combo_num % 25 == 0:
                        sys.stdout.flush()
                        print(f"  Progress: {combo_num}/{total_combos} "
                              f"(best so far: {best_robustness:.4f})")

    results.sort(key=lambda x: x["robustness"], reverse=True)

    # ── Export block log ───────────────────────────────────────────────────────
    log_file = f"COMB002_phase1_{asset}_{timeframe}_block_{block_num}_log.csv"
    with open(log_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\n  [OK] {log_file}")

    # ── Export top 10 ─────────────────────────────────────────────────────────
    top10_file = f"COMB002_phase1_{asset}_{timeframe}_block_{block_num}_top10.csv"
    with open(top10_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results[:10])
    print(f"  [OK] {top10_file}")

    # ── Export best params JSON ────────────────────────────────────────────────
    best_dict = None
    if best_params:
        trades_a = next(
            (r["phase_a_trades"] for r in results
             if r["smooth_h"] == best_params.stpmt_smooth_h
             and r["smooth_b"] == best_params.stpmt_smooth_b), 0)
        best_dict = {
            "strategy":              "COMB_002_IMPULSE",
            "asset":                 asset,
            "timeframe":             timeframe,
            "phase":                 1,
            "block":                 block_num,
            "stpmt_smooth_h":        best_params.stpmt_smooth_h,
            "stpmt_smooth_b":        best_params.stpmt_smooth_b,
            "stpmt_distance_max_h":  best_params.stpmt_distance_max_h,
            "stpmt_distance_max_l":  best_params.stpmt_distance_max_l,
            "robustness":            round(best_robustness, 4),
            "robustness_pass":       best_robustness >= ROBUSTNESS_THRESHOLD,
            "min_trades_pass":       trades_a >= MIN_TRADES_PHASE_A,
        }
        best_file = f"COMB002_phase1_{asset}_{timeframe}_block_{block_num}_best_params.json"
        with open(best_file, "w") as fh:
            json.dump(best_dict, fh, indent=2)
        print(f"  [OK] {best_file}")

    status = "PASS" if best_robustness >= ROBUSTNESS_THRESHOLD else "FAIL"
    print(f"\n  Block {block_num} result: robustness={best_robustness:.4f} [{status}]")

    return results, best_dict


def main():
    parser = argparse.ArgumentParser(
        description="COMB_002 IMPULSE Phase 1 Multi-Asset Runner"
    )
    parser.add_argument("--asset",     required=True,  choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True,  choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument(
        "--block", type=int, choices=[1, 2, 3, 4, 5], default=None,
        help="Run a specific block (1-5). Omit to run all 5 blocks sequentially."
    )
    args = parser.parse_args()

    asset, timeframe = args.asset, args.timeframe

    # ── Locate data files ──────────────────────────────────────────────────────
    phase_a_file, phase_b_file = get_data_filenames(asset, timeframe)

    print(f"\n{'='*80}")
    print(f"COMB_002 IMPULSE | Phase 1 Signal Optimization")
    print(f"Asset: {asset}  |  Timeframe: {timeframe}")
    print(f"Phase A data: {phase_a_file}")
    print(f"Phase B data: {phase_b_file}")
    print(f"Grid: 5×5×5×5 = 625 combos  |  5 blocks × 125 combos each")
    print(f"Success threshold: Robustness >= {ROBUSTNESS_THRESHOLD}")
    print(f"{'='*80}")

    if not Path(phase_a_file).exists():
        print(f"[ERROR] {phase_a_file} not found. Check working directory.")
        sys.exit(1)
    if not Path(phase_b_file).exists():
        print(f"[ERROR] {phase_b_file} not found. Check working directory.")
        sys.exit(1)

    print("\nLoading data...")
    phase_a_rows = load_ohlc_csv(phase_a_file)
    phase_b_rows = load_ohlc_csv(phase_b_file)
    print(f"Phase A: {len(phase_a_rows):,} rows  |  Phase B: {len(phase_b_rows):,} rows")

    # ── Run blocks ─────────────────────────────────────────────────────────────
    blocks_to_run = [args.block] if args.block else [1, 2, 3, 4, 5]
    all_results   = []
    block_bests   = []

    for block_num in blocks_to_run:
        smooth_h_values = [SMOOTH_H_RANGE[block_num - 1]]
        results, best = run_block(
            block_num, smooth_h_values,
            phase_a_rows, phase_b_rows,
            asset, timeframe
        )
        all_results.extend(results)
        if best:
            block_bests.append(best)

    # ── Consolidated output (only when all blocks ran) ─────────────────────────
    if args.block is None and all_results:
        all_results.sort(key=lambda x: x["robustness"], reverse=True)

        full_log = f"COMB002_phase1_{asset}_{timeframe}_full_log.csv"
        with open(full_log, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)

        top10_log = f"COMB002_phase1_{asset}_{timeframe}_top10.csv"
        with open(top10_log, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results[:10])

        best_overall = max(block_bests, key=lambda x: x["robustness"])
        best_file = f"COMB002_phase1_{asset}_{timeframe}_best_params.json"
        with open(best_file, "w") as fh:
            json.dump(best_overall, fh, indent=2)

        status = ">>> PASS <<<" if best_overall["robustness"] >= ROBUSTNESS_THRESHOLD else "!!! FAIL !!!"
        print(f"\n{'='*80}")
        print(f"PHASE 1 COMPLETE: {asset} {timeframe} [{status}]")
        print(f"Best signal params:")
        print(f"  stpmt_smooth_h       = {best_overall['stpmt_smooth_h']}")
        print(f"  stpmt_smooth_b       = {best_overall['stpmt_smooth_b']}")
        print(f"  stpmt_distance_max_h = {best_overall['stpmt_distance_max_h']}")
        print(f"  stpmt_distance_max_l = {best_overall['stpmt_distance_max_l']}")
        print(f"  robustness           = {best_overall['robustness']:.4f}")
        print(f"Output: {best_file}")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
