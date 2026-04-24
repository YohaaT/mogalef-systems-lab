"""Phase 1 Optimization Block Runner for COMB_002 IMPULSE - 5 blocks x 125 combos each

Strategy: Vary smooth_h in blocks
- Block 1: smooth_h=1 (125 combos: smooth_b×dist_h×dist_l = 5×5×5)
- Block 2: smooth_h=2 (125 combos)
- Block 3: smooth_h=3 (125 combos)
- Block 4: smooth_h=4 (125 combos)
- Block 5: smooth_h=5 (125 combos)

Note: IMPULSE differs from TREND in:
- NO Trend Filter (catches impulses in all regimes)
- TimeStop = 15 bars (shorter)
- SuperStop instead of Stop Inteligente
"""

import csv
import json
from pathlib import Path
from COMB_002_IMPULSE_V1 import Comb002ImpulseStrategy, Comb002ImpulseParams, load_ohlc_csv

# Parameter ranges
smooth_h_range = [1, 2, 3, 4, 5]
smooth_b_range = [1, 2, 3, 4, 5]
distance_max_h_range = [50, 100, 150, 200, 300]
distance_max_l_range = [50, 100, 150, 200, 300]


def run_block(block_num: int, smooth_h_values: list, phase_a_rows: list, phase_b_rows: list):
    """Run optimization for a specific block of smooth_h values."""

    print(f"\n{'='*80}")
    print(f"PHASE 1 IMPULSE OPTIMIZATION - BLOCK {block_num}")
    print(f"{'='*80}")
    print(f"smooth_h values: {smooth_h_values}")

    results = []
    best_robustness = 0
    best_params = None
    combo_num = 0
    total_combos = len(smooth_h_values) * len(smooth_b_range) * len(distance_max_h_range) * len(distance_max_l_range)

    print(f"Total combos in block: {total_combos}\n")

    # Test all combinations for this block
    for smooth_h in smooth_h_values:
        for smooth_b in smooth_b_range:
            for dist_max_h in distance_max_h_range:
                for dist_max_l in distance_max_l_range:
                    combo_num += 1

                    # Create params (lock other components to defaults)
                    params = Comb002ImpulseParams(
                        # Signal (VARIED)
                        stpmt_smooth_h=smooth_h,
                        stpmt_smooth_b=smooth_b,
                        stpmt_distance_max_h=dist_max_h,
                        stpmt_distance_max_l=dist_max_l,
                        # Contexto - Horaire (DEFAULT)
                        horaire_allowed_hours_utc=list(range(9, 16)),
                        # Contexto - Volatility (DEFAULT)
                        volatility_atr_min=0.0,
                        volatility_atr_max=500.0,
                        # Exits - Scalping Target (DEFAULT)
                        scalping_target_quality=2,
                        scalping_target_recent_volat=2,
                        scalping_target_ref_volat=20,
                        scalping_target_coef_volat=3.0,
                        # Exits - TimeStop (DEFAULT - 15 bars for impulse)
                        timescan_bars=15,
                        # Stops - SuperStop (DEFAULT)
                        superstop_quality=2,
                        superstop_coef_volat=3.0,
                    )

                    # Run Phase A
                    strategy = Comb002ImpulseStrategy(params)
                    result_a = strategy.run(phase_a_rows)

                    # Run Phase B
                    result_b = strategy.run(phase_b_rows)

                    # Calculate robustness
                    robustness = result_b.profit_factor / result_a.profit_factor if result_a.profit_factor > 0 else 0

                    # Store result
                    results.append({
                        "block": block_num,
                        "combo": combo_num,
                        "smooth_h": smooth_h,
                        "smooth_b": smooth_b,
                        "dist_max_h": dist_max_h,
                        "dist_max_l": dist_max_l,
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
                        print(f"[{combo_num}/{total_combos}] NEW BEST: smooth_h={smooth_h}, smooth_b={smooth_b}, dist={dist_max_h}/{dist_max_l} -> Robustness={robustness:.4f}")

                    # Progress every 25 combos
                    if combo_num % 25 == 0:
                        print(f"Progress: {combo_num}/{total_combos}")

    # Sort by robustness
    results.sort(key=lambda x: x["robustness"], reverse=True)

    # Export block results
    block_filename = f"phase1_impulse_optimization_block_{block_num}_log.csv"
    with open(block_filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OK] {block_filename}")

    # Export block top 10
    top_10 = results[:10]
    block_top_filename = f"phase1_impulse_optimization_block_{block_num}_top10.csv"
    with open(block_top_filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=top_10[0].keys())
        writer.writeheader()
        writer.writerows(top_10)
    print(f"[OK] {block_top_filename}")

    # Export block best params
    if best_params:
        best_params_dict = {
            "block": block_num,
            "stpmt_smooth_h": best_params.stpmt_smooth_h,
            "stpmt_smooth_b": best_params.stpmt_smooth_b,
            "stpmt_distance_max_h": best_params.stpmt_distance_max_h,
            "stpmt_distance_max_l": best_params.stpmt_distance_max_l,
            "robustness": best_robustness,
        }

        block_best_filename = f"phase1_impulse_optimization_block_{block_num}_best_params.json"
        with open(block_best_filename, "w") as f:
            json.dump(best_params_dict, f, indent=2)
        print(f"[OK] {block_best_filename}")

    return results, best_params_dict if best_params else None


def main():
    """Main entry point - loads data and runs appropriate block."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python phase1_impulse_optimization_block_runner.py <block_number>")
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

    # Get smooth_h values for this block
    smooth_h_values = [smooth_h_range[block_num - 1]]

    # Run block
    results, best_params = run_block(block_num, smooth_h_values, phase_a_rows, phase_b_rows)

    print(f"\n{'='*80}")
    print(f"BLOCK {block_num} COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
