"""Combine Phase 1 optimization block results into unified output files."""

import csv
import json
from pathlib import Path

def combine_block_results():
    """Combine all block results into final optimization files."""

    print("="*80)
    print("COMBINING PHASE 1 BLOCK RESULTS")
    print("="*80)

    all_results = []
    all_best_params = []

    # Read each block's results
    for block_num in range(1, 6):
        block_log_file = f"phase1_optimization_block_{block_num}_log.csv"
        block_best_file = f"phase1_optimization_block_{block_num}_best_params.json"

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
    full_log_file = "phase1_optimization_full_log.csv"
    with open(full_log_file, "w", newline="") as f:
        # Remove the temporary float column for export
        fieldnames = [k for k in all_results[0].keys() if k != "robustness_float"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in all_results:
            row = {k: v for k, v in result.items() if k != "robustness_float"}
            writer.writerow(row)
    print(f"[OK] {full_log_file} ({len(all_results)} combos)")

    # Export top 10
    top_10 = all_results[:10]
    top_10_file = "phase1_optimization_top10.csv"
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
        "stpmt_smooth_h": int(best_overall["smooth_h"]),
        "stpmt_smooth_b": int(best_overall["smooth_b"]),
        "stpmt_distance_max_h": int(best_overall["dist_max_h"]),
        "stpmt_distance_max_l": int(best_overall["dist_max_l"]),
        "robustness": float(best_overall["robustness"]),
        "phase_a_pf": float(best_overall["phase_a_pf"]),
        "phase_b_pf": float(best_overall["phase_b_pf"]),
    }

    best_params_file = "phase1_best_params.json"
    with open(best_params_file, "w") as f:
        json.dump(best_overall_params, f, indent=2)
    print(f"[OK] {best_params_file}")

    # Print summary
    print("\n" + "="*80)
    print("PHASE 1 OPTIMIZATION SUMMARY")
    print("="*80)
    print(f"\nTop 10 Combos (sorted by Robustness):\n")
    print(f"{'Rank':<5} {'smooth_h':<10} {'smooth_b':<10} {'dist_h':<8} {'dist_l':<8} {'Phase A PF':<12} {'Phase B PF':<12} {'Robustness':<12}")
    print("-" * 80)

    for i, combo in enumerate(top_10, 1):
        print(f"{i:<5} {combo['smooth_h']:<10} {combo['smooth_b']:<10} {combo['dist_max_h']:<8} {combo['dist_max_l']:<8} {combo['phase_a_pf']:<12} {combo['phase_b_pf']:<12} {combo['robustness']:<12}")

    print("\n" + "="*80)
    print("BEST COMBO SELECTED:")
    print("="*80)
    print(f"smooth_h: {best_overall_params['stpmt_smooth_h']}")
    print(f"smooth_b: {best_overall_params['stpmt_smooth_b']}")
    print(f"distance_max_h: {best_overall_params['stpmt_distance_max_h']}")
    print(f"distance_max_l: {best_overall_params['stpmt_distance_max_l']}")
    print(f"Robustness: {best_overall_params['robustness']:.4f}")
    print(f"Phase A PF: {best_overall_params['phase_a_pf']:.4f}")
    print(f"Phase B PF: {best_overall_params['phase_b_pf']:.4f}")

    print("\n" + "="*80)
    print("PHASE 1 OPTIMIZATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    combine_block_results()
