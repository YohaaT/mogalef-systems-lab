"""Combine Phase 1 breakout optimization block results into unified output files."""

import csv
import json
from pathlib import Path

def combine_block_results():
    """Combine all block results into final optimization files."""

    print("="*80)
    print("COMBINING PHASE 1 BREAKOUT BLOCK RESULTS")
    print("="*80)

    all_results = []
    all_best_params = []

    # Read each block's results
    for block_num in range(1, 6):
        block_log_file = f"phase1_breakout_optimization_block_{block_num}_log.csv"
        block_best_file = f"phase1_breakout_optimization_block_{block_num}_best_params.json"

        # Read block log
        try:
            with open(block_log_file, "r") as f:
                reader = csv.DictReader(f)
                block_results = list(reader)
                all_results.extend(block_results)
                print(f"[OK] Loaded {len(block_results)} results from Block {block_num}")
        except FileNotFoundError:
            print(f"[WARN] Block {block_num} log not found: {block_log_file}")

        # Read block best params
        try:
            with open(block_best_file, "r") as f:
                best = json.load(f)
                all_best_params.append(best)
                print(f"[OK] Loaded best params from Block {block_num}")
        except FileNotFoundError:
            print(f"[WARN] Block {block_num} best params not found: {block_best_file}")

    if not all_results:
        print("[ERROR] No results to combine!")
        return

    # Sort all results by robustness
    print(f"\nSorting {len(all_results)} total results by robustness...")

    # Convert robustness to float for sorting
    for result in all_results:
        result["robustness_float"] = float(result["robustness"])

    all_results.sort(key=lambda x: x["robustness_float"], reverse=True)

    # Export full combined log
    print("\nExporting combined results...")
    full_log_file = "phase1_breakout_optimization_full_log.csv"
    with open(full_log_file, "w", newline="") as f:
        fieldnames = [k for k in all_results[0].keys() if k != "robustness_float"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in all_results:
            row = {k: v for k, v in result.items() if k != "robustness_float"}
            writer.writerow(row)
    print(f"[OK] {full_log_file} ({len(all_results)} combos)")

    # Export top 10
    top_10 = all_results[:10]
    top_10_file = "phase1_breakout_optimization_top10.csv"
    with open(top_10_file, "w", newline="") as f:
        fieldnames = [k for k in top_10[0].keys() if k != "robustness_float"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in top_10:
            row = {k: v for k, v in result.items() if k != "robustness_float"}
            writer.writerow(row)
    print(f"[OK] {top_10_file} (top 10 by robustness)")

    # Find overall best
    best_overall = all_results[0]
    best_overall_params = {
        "breakout_lookback_high": int(best_overall["lookback_h"]),
        "breakout_lookback_low": int(best_overall["lookback_l"]),
        "breakout_min_breakout_points": float(best_overall["min_breakout"]),
        "stop_loss_points": float(best_overall["stop_loss"]),
        "robustness": float(best_overall["robustness"]),
        "phase_a_pf": float(best_overall["phase_a_pf"]),
        "phase_b_pf": float(best_overall["phase_b_pf"]),
    }

    best_params_file = "phase1_breakout_best_params.json"
    with open(best_params_file, "w") as f:
        json.dump(best_overall_params, f, indent=2)
    print(f"[OK] {best_params_file}")

    # Print summary
    print("\n" + "="*80)
    print("PHASE 1 BREAKOUT OPTIMIZATION SUMMARY")
    print("="*80)
    print(f"\nTop 10 Combos (sorted by Robustness):\n")
    print(f"{'Rank':<5} {'LB_H':<6} {'LB_L':<6} {'Min_B':<7} {'Stop':<6} {'Phase A PF':<12} {'Phase B PF':<12} {'Robustness':<12}")
    print("-" * 80)

    for i, combo in enumerate(top_10, 1):
        print(f"{i:<5} {combo['lookback_h']:<6} {combo['lookback_l']:<6} {combo['min_breakout']:<7} {combo['stop_loss']:<6} {combo['phase_a_pf']:<12} {combo['phase_b_pf']:<12} {combo['robustness']:<12}")

    print("\n" + "="*80)
    print("BEST COMBO SELECTED:")
    print("="*80)
    print(f"breakout_lookback_high: {best_overall_params['breakout_lookback_high']}")
    print(f"breakout_lookback_low: {best_overall_params['breakout_lookback_low']}")
    print(f"breakout_min_breakout_points: {best_overall_params['breakout_min_breakout_points']}")
    print(f"stop_loss_points: {best_overall_params['stop_loss_points']}")
    print(f"Robustness: {best_overall_params['robustness']:.4f}")
    print(f"Phase A PF: {best_overall_params['phase_a_pf']:.4f}")
    print(f"Phase B PF: {best_overall_params['phase_b_pf']:.4f}")

    print("\n" + "="*80)
    print("PHASE 1 BREAKOUT OPTIMIZATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    combine_block_results()
