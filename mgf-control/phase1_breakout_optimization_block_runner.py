"""Phase 1 Breakout Optimization Block Runner - 5 blocks x 125 combos each

Strategy: Vary breakout_lookback_high in blocks
- Block 1: lookback_high=5 (125 combos: lookback_low×min_breakout_pts×stop×target)
- Block 2: lookback_high=10 (125 combos)
- Block 3: lookback_high=15 (125 combos)
- Block 4: lookback_high=20 (125 combos)
- Block 5: lookback_high=25 (125 combos)

Note: Optimizing signal quality by varying lookback periods for breakout detection
"""

import csv
import json
from pathlib import Path
from COMB_003_BREAKOUT_V1 import Comb003BreakoutStrategy, Comb003BreakoutParams, load_ohlc_csv

# Parameter ranges
lookback_high_range = [5, 10, 15, 20, 25]
lookback_low_range = [5, 10, 15, 20]
min_breakout_points_range = [2.0, 5.0, 10.0, 15.0, 20.0]
stop_loss_range = [10.0, 15.0, 20.0, 25.0, 30.0]

def run_block(block_num: int, lookback_high_values: list, phase_a_rows: list, phase_b_rows: list):
    """Run optimization for a specific block of lookback_high values."""

    print(f"\n{'='*80}")
    print(f"PHASE 1 BREAKOUT OPTIMIZATION - BLOCK {block_num}")
    print(f"{'='*80}")
    print(f"lookback_high values: {lookback_high_values}")

    results = []
    best_robustness = 0
    best_params = None
    combo_num = 0
    total_combos = len(lookback_high_values) * len(lookback_low_range) * len(min_breakout_points_range) * len(stop_loss_range)

    print(f"Total combos in block: {total_combos}\n")

    # Test all combinations for this block
    for lookback_h in lookback_high_values:
        for lookback_l in lookback_low_range:
            for min_breakout in min_breakout_points_range:
                for stop_loss in stop_loss_range:
                    combo_num += 1

                    # Create params (lock other components to defaults)
                    params = Comb003BreakoutParams(
                        # Signal (VARIED)
                        breakout_lookback_high=lookback_h,
                        breakout_lookback_low=lookback_l,
                        breakout_min_breakout_points=min_breakout,
                        # Contexto - Neutral Zone (DEFAULT)
                        neutralzone_mme_period=50,
                        neutralzone_ret_window=90,
                        # Contexto - Trend Filter (DEFAULT)
                        trend_r1=1,
                        trend_r2=90,
                        trend_r3=150,
                        # Contexto - Horaire (DEFAULT)
                        horaire_allowed_hours_utc=list(range(8, 22)),
                        # Exits (VARIED STOP, FIXED TARGET)
                        stop_loss_points=stop_loss,
                        profit_target_points=80.0,  # Fixed 1:4 ratio (for now)
                    )

                    # Run Phase A
                    strategy = Comb003BreakoutStrategy(params)
                    result_a = strategy.run(phase_a_rows)

                    # Run Phase B
                    result_b = strategy.run(phase_b_rows)

                    # Calculate robustness
                    robustness = result_b.profit_factor / result_a.profit_factor if result_a.profit_factor > 0 else 0

                    # Store result
                    results.append({
                        "block": block_num,
                        "combo": combo_num,
                        "lookback_h": lookback_h,
                        "lookback_l": lookback_l,
                        "min_breakout": min_breakout,
                        "stop_loss": stop_loss,
                        "phase_a_pf": round(result_a.profit_factor, 4),
                        "phase_a_wr": round(result_a.win_rate, 4),
                        "phase_a_trades": len(result_a.trades),
                        "phase_a_equity": round(result_a.equity_points, 2),
                        "phase_b_pf": round(result_b.profit_factor, 4),
                        "phase_b_wr": round(result_b.win_rate, 4),
                        "phase_b_trades": len(result_b.trades),
                        "phase_b_equity": round(result_b.equity_points, 2),
                        "robustness": round(robustness, 4),
                    })

                    # Track best
                    if robustness > best_robustness:
                        best_robustness = robustness
                        best_params = params
                        print(f"[{combo_num}/{total_combos}] NEW BEST: lookback={lookback_h}/{lookback_l}, min_break={min_breakout}, stop={stop_loss} -> Robustness={robustness:.4f}")

                    # Progress every 25 combos
                    if combo_num % 25 == 0:
                        print(f"Progress: {combo_num}/{total_combos}")

    # Sort by robustness
    results.sort(key=lambda x: x["robustness"], reverse=True)

    # Export block results
    block_filename = f"phase1_breakout_optimization_block_{block_num}_log.csv"
    with open(block_filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OK] {block_filename}")

    # Export block top 10
    top_10 = results[:10]
    block_top_filename = f"phase1_breakout_optimization_block_{block_num}_top10.csv"
    with open(block_top_filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=top_10[0].keys())
        writer.writeheader()
        writer.writerows(top_10)
    print(f"[OK] {block_top_filename}")

    # Export block best params
    if best_params:
        best_params_dict = {
            "block": block_num,
            "breakout_lookback_high": best_params.breakout_lookback_high,
            "breakout_lookback_low": best_params.breakout_lookback_low,
            "breakout_min_breakout_points": best_params.breakout_min_breakout_points,
            "stop_loss_points": best_params.stop_loss_points,
            "robustness": best_robustness,
        }

        block_best_filename = f"phase1_breakout_optimization_block_{block_num}_best_params.json"
        with open(block_best_filename, "w") as f:
            json.dump(best_params_dict, f, indent=2)
        print(f"[OK] {block_best_filename}")

    return results, best_params_dict if best_params else None


def main():
    """Main entry point - loads data and runs appropriate block."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python phase1_breakout_optimization_block_runner.py <block_number>")
        print("block_number: 1-5")
        sys.exit(1)

    block_num = int(sys.argv[1])
    if block_num < 1 or block_num > 5:
        print("Invalid block number. Must be 1-5")
        sys.exit(1)

    # Load data
    print("Loading Phase A and Phase B data...")
    phase_a_rows = load_ohlc_csv("YM_phase_A_clean.csv")
    phase_b_rows = load_ohlc_csv("YM_phase_B_clean.csv")
    print(f"Phase A: {len(phase_a_rows)} rows")
    print(f"Phase B: {len(phase_b_rows)} rows")

    # Get lookback_high values for this block
    lookback_high_values = [lookback_high_range[block_num - 1]]

    # Run block
    results, best_params = run_block(block_num, lookback_high_values, phase_a_rows, phase_b_rows)

    print(f"\n{'='*80}")
    print(f"BLOCK {block_num} COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
