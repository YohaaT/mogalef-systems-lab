"""Phase 2 Full Optimizer - Master script

Executes all Phase 2 sub-phases in sequence:
1. Phase 2a: Trend Filter optimization (2 blocks of trend_r1/r2/r3)
2. Phase 2b: Horaire optimization (6 sequential UTC hour profiles)
3. Phase 2c: Volatility optimization (5 sequential ATR bands)
4. Consolidate all results

Each phase locks previous results.

Usage:
    python run_phase2_full.py
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """Run a command and report progress."""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"{'='*80}")
    print(f"Command: {cmd}\n")

    t0 = time.time()
    try:
        result = subprocess.run(cmd, shell=True, check=True)
        elapsed = time.time() - t0
        print(f"\n[OK] {description} completed in {elapsed:.1f}s")
        return True
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - t0
        print(f"\n[FAIL] {description} failed after {elapsed:.1f}s")
        print(f"Exit code: {e.returncode}")
        return False


def main():
    print("\n" + "="*80)
    print("PHASE 2 FULL OPTIMIZATION - MASTER RUNNER")
    print("="*80)
    print("Locks from Phase 1:")
    print("  stpmt_smooth_h: 3")
    print("  stpmt_smooth_b: 2")
    print("  stpmt_distance_max_h: 50")
    print("  stpmt_distance_max_l: 50")

    # Verify data files exist
    print("\n[PRE-CHECK] Verifying data files...")
    for fname in ["YM_phase_A_clean.csv", "YM_phase_B_clean.csv", "phase1_best_params.json"]:
        if not Path(fname).exists():
            print(f"[ERROR] Missing: {fname}")
            return 1
    print("[OK] All required files present\n")

    # Phase 2a: Trend Filter - Block 1
    if not run_command(
        "python phase2a_trend_optimization_block_runner_vec.py 1",
        "[PHASE 2a-1] Trend Filter Optimization - Block 1 (r1=[1,2], 60 combos)"
    ):
        return 1

    # Phase 2a: Trend Filter - Block 2
    if not run_command(
        "python phase2a_trend_optimization_block_runner_vec.py 2",
        "[PHASE 2a-2] Trend Filter Optimization - Block 2 (r1=[3,4,5], 90 combos)"
    ):
        return 1

    # Phase 2a: Consolidate blocks
    if not run_command(
        "python phase2a_consolidate_blocks.py",
        "[PHASE 2a-C] Consolidating Block 1 + Block 2 results"
    ):
        return 1

    # Phase 2b: Horaire
    if not run_command(
        "python phase2b_horaire_optimization.py",
        "[PHASE 2b] Horaire Optimization (6 sequential UTC hour profiles)"
    ):
        return 1

    # Phase 2c: Volatility
    if not run_command(
        "python phase2c_volatility_optimization.py",
        "[PHASE 2c] Volatility Optimization (5 sequential ATR bands)"
    ):
        return 1

    # Phase 2 Consolidate
    if not run_command(
        "python phase2_combine_results.py",
        "[PHASE 2-FINAL] Consolidating all Phase 2 sub-phases"
    ):
        return 1

    # Summary
    print(f"\n{'='*80}")
    print("PHASE 2 COMPLETE")
    print(f"{'='*80}")
    print("\nGenerated files:")
    print("  ✓ phase2a_trend_optimization_block_1_log.csv (60 combos)")
    print("  ✓ phase2a_trend_optimization_block_2_log.csv (90 combos)")
    print("  ✓ phase2a_trend_full_log.csv (150 combos, consolidated)")
    print("  ✓ phase2a_trend_best_params.json")
    print("  ✓ phase2b_horaire_optimization_log.csv (6 profiles)")
    print("  ✓ phase2b_horaire_best_params.json")
    print("  ✓ phase2c_volatility_optimization_log.csv (5 bands)")
    print("  ✓ phase2c_volatility_best_params.json")
    print("  ✓ phase2_best_params.json (Phase 1+2 combined)")
    print("  ✓ phase3_summary.json (locked params ready for Phase 3)")
    print(f"\n{'='*80}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
