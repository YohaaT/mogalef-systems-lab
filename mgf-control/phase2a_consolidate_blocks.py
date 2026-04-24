"""Phase 2a Consolidation: Merge Block 1 and Block 2 results

Reads best params from:
- phase2a_trend_optimization_block_1_best_params.json
- phase2a_trend_optimization_block_2_best_params.json

Reads full logs from:
- phase2a_trend_optimization_block_1_log.csv
- phase2a_trend_optimization_block_2_log.csv

Outputs:
- phase2a_trend_best_params.json (best overall across both blocks)
- phase2a_trend_full_log.csv (all 150 combos sorted by robustness)
"""

import csv
import json
from pathlib import Path


def load_json(filepath: str) -> dict:
    """Load JSON file, raise if not found."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath) as f:
        return json.load(f)


def load_csv(filepath: str) -> list:
    """Load CSV file, return list of dicts."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath) as f:
        return list(csv.DictReader(f))


def main():
    print("\n" + "="*80)
    print("PHASE 2a CONSOLIDATION - MERGING BLOCK 1 + BLOCK 2")
    print("="*80)

    # Load block best params
    print("\n[1] Loading Block 1 best...")
    try:
        block1_best = load_json("phase2a_trend_optimization_block_1_best_params.json")
        print(f"    r1={block1_best['trend_r1']}, r2={block1_best['trend_r2']}, r3={block1_best['trend_r3']}")
        print(f"    Robustness: {block1_best['robustness']:.4f}")
    except FileNotFoundError as e:
        print(f"    [ERROR] {e}")
        return 1

    print("\n[2] Loading Block 2 best...")
    try:
        block2_best = load_json("phase2a_trend_optimization_block_2_best_params.json")
        print(f"    r1={block2_best['trend_r1']}, r2={block2_best['trend_r2']}, r3={block2_best['trend_r3']}")
        print(f"    Robustness: {block2_best['robustness']:.4f}")
    except FileNotFoundError as e:
        print(f"    [ERROR] {e}")
        return 1

    # Determine overall best
    if float(block1_best["robustness"]) > float(block2_best["robustness"]):
        best_overall = block1_best
        best_block = 1
    else:
        best_overall = block2_best
        best_block = 2

    print(f"\n[3] Overall best: Block {best_block} with robustness {best_overall['robustness']:.4f}")

    # Load full logs and merge
    print("\n[4] Loading and merging full logs...")
    try:
        block1_log = load_csv("phase2a_trend_optimization_block_1_log.csv")
        block2_log = load_csv("phase2a_trend_optimization_block_2_log.csv")
        print(f"    Block 1: {len(block1_log)} combos")
        print(f"    Block 2: {len(block2_log)} combos")

        all_results = block1_log + block2_log
        print(f"    Total: {len(all_results)} combos")

        # Sort by robustness descending
        all_results.sort(key=lambda x: float(x["robustness"]), reverse=True)

        # Export consolidated log
        full_log_file = "phase2a_trend_full_log.csv"
        with open(full_log_file, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=all_results[0].keys())
            w.writeheader()
            w.writerows(all_results)
        print(f"    [OK] {full_log_file} (sorted by robustness)")

    except FileNotFoundError as e:
        print(f"    [ERROR] {e}")
        return 1

    # Export best params JSON
    print("\n[5] Saving consolidated best params...")
    best_dict = {
        "block": best_overall["block"],
        "trend_r1": best_overall["trend_r1"],
        "trend_r2": best_overall["trend_r2"],
        "trend_r3": best_overall["trend_r3"],
        "robustness": best_overall["robustness"],
        "phase_a_pf": best_overall["phase_a_pf"],
        "phase_b_pf": best_overall["phase_b_pf"],
    }
    best_file = "phase2a_trend_best_params.json"
    with open(best_file, "w") as f:
        json.dump(best_dict, f, indent=2)
    print(f"    [OK] {best_file}")

    # Print summary
    print("\n" + "="*80)
    print("PHASE 2a CONSOLIDATION COMPLETE")
    print("="*80)
    print(f"Best: r1={best_overall['trend_r1']}, r2={best_overall['trend_r2']}, r3={best_overall['trend_r3']}")
    print(f"Robustness: {best_overall['robustness']:.4f}")
    print(f"Phase A PF: {best_overall['phase_a_pf']:.4f}")
    print(f"Phase B PF: {best_overall['phase_b_pf']:.4f}")
    print("="*80)

    return 0


if __name__ == "__main__":
    exit(main())
