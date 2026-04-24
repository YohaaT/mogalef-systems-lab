#!/usr/bin/env python3
"""
Asset Optimization Orchestrator — COMB_001_TREND
Runs all 4 phases for a given asset by temporarily mapping
{ASSET}_phase_A/B_5m.csv → YM_phase_A/B_5m.csv (reusing all scripts as-is).

Usage:
    python3 run_asset_optimization.py MNQ
    python3 run_asset_optimization.py FDAX
    python3 run_asset_optimization.py ES

Each run overwrites intermediate phase files, then saves final
results with asset-specific suffix.
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ASSET = sys.argv[1].upper() if len(sys.argv) > 1 else "MNQ"
BASE = Path(__file__).parent
LOG = BASE / f"run_{ASSET}_optimization.log"
START = datetime.now()


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def run(cmd, desc, timeout=7200):
    log(f"START: {desc}")
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(BASE), timeout=timeout
    )
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            print(f"    {line}", flush=True)
    if result.returncode != 0:
        log(f"FAILED: {desc}", "ERROR")
        if result.stderr:
            log(result.stderr[-500:], "ERROR")
        raise RuntimeError(f"{desc} failed (exit {result.returncode})")
    log(f"DONE: {desc}", "OK")
    return result.stdout


def swap_csvs_to_asset(asset):
    """Copy {asset}_phase_A/B_5m.csv → YM_phase_A/B_5m.csv"""
    log(f"Swapping CSVs to {asset} data")
    shutil.copy(BASE / f"{asset}_phase_A_5m.csv", BASE / "YM_phase_A_5m.csv")
    shutil.copy(BASE / f"{asset}_phase_B_5m.csv", BASE / "YM_phase_B_5m.csv")
    log(f"CSVs swapped: {asset} data now at YM_phase_*.csv")


def save_phase_result(src_name, dest_name):
    src = BASE / src_name
    dest = BASE / dest_name
    if src.exists():
        shutil.copy(src, dest)
        log(f"Saved: {src_name} → {dest_name}")
    else:
        log(f"NOT FOUND: {src_name}", "WARN")


def main():
    log("=" * 70)
    log(f"COMB_001_TREND OPTIMIZATION: {ASSET}")
    log(f"Started: {START.strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 70)

    # Step 0: Swap CSVs
    swap_csvs_to_asset(ASSET)

    # ── PHASE 1: SIGNAL ─────────────────────────────────────────────────────
    log("\n── PHASE 1: SIGNAL OPTIMIZATION (625 combos split) ──")

    # Clean stale phase1 json to avoid reuse
    for f in ["phase1_5m_signal_block_1_best_params.json",
              "bo_phase1_5m_signal_block_2_best_params.json",
              "phase1_5m_best_params.json"]:
        if (BASE / f).exists():
            (BASE / f).unlink()

    # Block 2 on BO (450 combos)
    run(["python3", "phase1_5m_signal_block_runner.py", "2"],
        f"Phase 1 Block 2 (BO) — {ASSET}", timeout=3600)

    # Rename Block 2 output for consolidation
    save_phase_result("phase1_5m_signal_block_2_best_params.json",
                      "bo_phase1_5m_signal_block_2_best_params.json")

    # Block 1 result from TANK should already be in phase1_5m_signal_block_1_best_params.json
    # (copied from TANK by the calling script or SSH)
    # If not present, use Block 2 only
    if not (BASE / "phase1_5m_signal_block_1_best_params.json").exists():
        log("Block 1 (TANK) not found — using Block 2 only", "WARN")

    run(["python3", "phase1_5m_consolidate.py"],
        f"Phase 1 Consolidation — {ASSET}", timeout=60)

    save_phase_result("phase1_5m_best_params.json",
                      f"phase1_5m_{ASSET}_best_params.json")

    # ── PHASE 2: CONTEXTO ───────────────────────────────────────────────────
    log("\n── PHASE 2: CONTEXTO OPTIMIZATION ──")

    run(["python3", "phase2a_5m_trend_filter_optimizer.py"],
        f"Phase 2a Trend Filter — {ASSET}", timeout=1800)

    run(["python3", "phase2b_5m_horaire_optimizer.py"],
        f"Phase 2b Horaire — {ASSET}", timeout=600)

    run(["python3", "phase2c_5m_volatility_optimizer.py"],
        f"Phase 2c Volatility — {ASSET}", timeout=600)

    run(["python3", "phase2d_5m_weekday_filter_optimizer.py"],
        f"Phase 2d Weekday — {ASSET}", timeout=600)

    run(["python3", "phase2_5m_consolidate.py"],
        f"Phase 2 Consolidation — {ASSET}", timeout=60)

    save_phase_result("phase2_5m_best_params.json",
                      f"phase2_5m_{ASSET}_best_params.json")

    # ── PHASE 3: EXITS ──────────────────────────────────────────────────────
    log("\n── PHASE 3: EXITS OPTIMIZATION (16 combos) ──")

    run(["python3", "phase3_5m_exits_optimizer.py"],
        f"Phase 3 Exits — {ASSET}", timeout=600)

    save_phase_result("phase3_5m_exits_best_params.json",
                      f"phase3_5m_{ASSET}_best_params.json")

    # ── PHASE 4: STOPS ──────────────────────────────────────────────────────
    log("\n── PHASE 4: STOPS INTELLIGENT (42 combos) ──")

    # Clean stale files
    for f in ["phase4_5m_stops_block_1_best_params.json",
              "phase4_5m_stops_block_2_best_params.json",
              "phase4_5m_best_params.json"]:
        if (BASE / f).exists():
            (BASE / f).unlink()

    # Block 2 on BO (quality=3, 18 combos)
    run(["python3", "phase4_5m_stops_optimizer.py", "2"],
        f"Phase 4 Block 2 (BO) — {ASSET}", timeout=1800)

    # Block 1 from TANK (if available) — otherwise skip
    if not (BASE / "phase4_5m_stops_block_1_best_params.json").exists():
        log("Phase 4 Block 1 (TANK) not found — consolidating Block 2 only", "WARN")

    run(["python3", "phase4_5m_consolidate.py"],
        f"Phase 4 Consolidation — {ASSET}", timeout=60)

    save_phase_result("phase4_5m_best_params.json",
                      f"phase4_5m_{ASSET}_best_params.json")

    # ── FINAL CONSOLIDATION ─────────────────────────────────────────────────
    log("\n── FINAL CONSOLIDATION ──")

    run(["python3", "comb_001_trend_5m_final_consolidate.py"],
        f"Final Consolidation — {ASSET}", timeout=60)

    # Rename final output with asset tag
    final_src = BASE / "COMB_001_TREND_5m_FINAL_PARAMS.json"
    final_dst = BASE / f"COMB_001_TREND_5m_FINAL_PARAMS_{ASSET}.json"
    if final_src.exists():
        shutil.copy(final_src, final_dst)
        log(f"Final params saved → {final_dst.name}", "OK")

    # ── SUMMARY ─────────────────────────────────────────────────────────────
    elapsed = datetime.now() - START
    h, rem = divmod(int(elapsed.total_seconds()), 3600)
    m, s = divmod(rem, 60)

    log("\n" + "=" * 70)
    log(f"✅ {ASSET} OPTIMIZATION COMPLETE — {h:02d}:{m:02d}:{s:02d}", "OK")
    log("=" * 70)

    # Print final results
    if final_dst.exists():
        with open(final_dst) as f:
            d = json.load(f)
        log(f"Phase A PF: {d['validation']['phase_a_pf']}")
        log(f"Phase B PF: {d['validation']['phase_b_pf']}")
        log(f"Robustness: {d['validation']['final_robustness']:.4f}")


if __name__ == "__main__":
    main()
