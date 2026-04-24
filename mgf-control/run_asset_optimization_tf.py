#!/usr/bin/env python3
"""
Asset Optimization Orchestrator — Multi-Timeframe
Runs all 4 phases for a given asset AND timeframe.

Usage:
    python3 run_asset_optimization_tf.py MNQ 10    → MNQ on 10m bars
    python3 run_asset_optimization_tf.py FDAX 15   → FDAX on 15m bars
    python3 run_asset_optimization_tf.py ES 10     → ES on 10m bars

Strategy: maps {ASSET}_phase_A/B_{TF}m.csv → YM_phase_A/B_5m.csv
so all existing phase scripts work unchanged.
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ASSET = sys.argv[1].upper() if len(sys.argv) > 1 else "MNQ"
TF    = int(sys.argv[2])    if len(sys.argv) > 2 else 10
TF_LABEL = f"{TF}m"

BASE  = Path(__file__).parent
LOG   = BASE / f"run_{ASSET}_{TF_LABEL}_optimization.log"
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
            log(result.stderr[-800:], "ERROR")
        raise RuntimeError(f"{desc} failed (exit {result.returncode})")
    log(f"DONE: {desc}", "OK")
    return result.stdout


def swap_csvs(asset, tf_label):
    """Map {asset}_phase_A/B_{tf}m.csv → YM_phase_A/B_5m.csv"""
    src_a = BASE / f"{asset}_phase_A_{tf_label}.csv"
    src_b = BASE / f"{asset}_phase_B_{tf_label}.csv"

    if not src_a.exists():
        raise FileNotFoundError(
            f"Missing {src_a.name} — run: python3 prepare_multiframe.py {tf_label[:-1]} first")

    shutil.copy(src_a, BASE / "YM_phase_A_5m.csv")
    shutil.copy(src_b, BASE / "YM_phase_B_5m.csv")
    log(f"CSVs mapped: {asset} {tf_label} → YM_phase_*.csv")


def save(src_name, dest_name):
    src = BASE / src_name
    if src.exists():
        shutil.copy(src, BASE / dest_name)
        log(f"Saved: {src_name} → {dest_name}")
    else:
        log(f"NOT FOUND: {src_name}", "WARN")


def main():
    log("=" * 70)
    log(f"COMB_001_TREND OPTIMIZATION: {ASSET} @ {TF_LABEL}")
    log(f"Started: {START.strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 70)

    # Step 0: Map CSVs
    swap_csvs(ASSET, TF_LABEL)

    # ── PHASE 1 ──────────────────────────────────────────────────────────
    log("\n── PHASE 1: SIGNAL (625 combos) ──")
    for f in ["phase1_5m_signal_block_1_best_params.json",
              "bo_phase1_5m_signal_block_2_best_params.json",
              "phase1_5m_best_params.json"]:
        if (BASE / f).exists(): (BASE / f).unlink()

    run(["python3", "phase1_5m_signal_block_runner.py", "2"],
        f"Phase 1 Block2 BO — {ASSET} {TF_LABEL}", timeout=3600)

    save("phase1_5m_signal_block_2_best_params.json",
         "bo_phase1_5m_signal_block_2_best_params.json")

    if not (BASE / "phase1_5m_signal_block_1_best_params.json").exists():
        log("Block1 (TANK) not found — using Block2 only", "WARN")

    run(["python3", "phase1_5m_consolidate.py"],
        f"Phase 1 Consolidate — {ASSET} {TF_LABEL}")

    save("phase1_5m_best_params.json",
         f"phase1_{TF_LABEL}_{ASSET}_best_params.json")

    # ── PHASE 2 ──────────────────────────────────────────────────────────
    log("\n── PHASE 2: CONTEXTO ──")
    run(["python3", "phase2a_5m_trend_filter_optimizer.py"],
        f"Phase 2a TrendFilter — {ASSET} {TF_LABEL}", timeout=1800)
    run(["python3", "phase2b_5m_horaire_optimizer.py"],
        f"Phase 2b Horaire — {ASSET} {TF_LABEL}")
    run(["python3", "phase2c_5m_volatility_optimizer.py"],
        f"Phase 2c Volatility — {ASSET} {TF_LABEL}")
    run(["python3", "phase2d_5m_weekday_filter_optimizer.py"],
        f"Phase 2d Weekday — {ASSET} {TF_LABEL}")
    run(["python3", "phase2_5m_consolidate.py"],
        f"Phase 2 Consolidate — {ASSET} {TF_LABEL}")

    save("phase2_5m_best_params.json",
         f"phase2_{TF_LABEL}_{ASSET}_best_params.json")

    # ── PHASE 3 ──────────────────────────────────────────────────────────
    log("\n── PHASE 3: EXITS (16 combos) ──")
    run(["python3", "phase3_5m_exits_optimizer.py"],
        f"Phase 3 Exits — {ASSET} {TF_LABEL}")

    save("phase3_5m_exits_best_params.json",
         f"phase3_{TF_LABEL}_{ASSET}_best_params.json")

    # ── PHASE 4 ──────────────────────────────────────────────────────────
    log("\n── PHASE 4: STOPS INTELLIGENT ──")
    for f in ["phase4_5m_stops_block_1_best_params.json",
              "phase4_5m_stops_block_2_best_params.json",
              "phase4_5m_best_params.json"]:
        if (BASE / f).exists(): (BASE / f).unlink()

    run(["python3", "phase4_5m_stops_optimizer.py", "2"],
        f"Phase 4 Block2 BO — {ASSET} {TF_LABEL}", timeout=1800)

    if not (BASE / "phase4_5m_stops_block_1_best_params.json").exists():
        log("Phase 4 Block1 (TANK) not found — Block2 only", "WARN")

    run(["python3", "phase4_5m_consolidate.py"],
        f"Phase 4 Consolidate — {ASSET} {TF_LABEL}")

    save("phase4_5m_best_params.json",
         f"phase4_{TF_LABEL}_{ASSET}_best_params.json")

    # ── FINAL ─────────────────────────────────────────────────────────────
    log("\n── FINAL CONSOLIDATION ──")
    run(["python3", "comb_001_trend_5m_final_consolidate.py"],
        f"Final Consolidation — {ASSET} {TF_LABEL}")

    src  = BASE / "COMB_001_TREND_5m_FINAL_PARAMS.json"
    dest = BASE / f"COMB_001_TREND_{TF_LABEL}_FINAL_PARAMS_{ASSET}.json"
    if src.exists():
        # Patch timeframe label in the saved copy
        with open(src) as f:
            data = json.load(f)
        data["timeframe"] = f"{TF} minutes"
        data["asset"] = f"{ASSET} @ {TF_LABEL}"
        dest.write_text(json.dumps(data, indent=2))
        log(f"Final params → {dest.name}", "OK")

    # ── SUMMARY ───────────────────────────────────────────────────────────
    elapsed = datetime.now() - START
    h, rem  = divmod(int(elapsed.total_seconds()), 3600)
    m, s    = divmod(rem, 60)

    log("\n" + "=" * 70)
    log(f"✅ {ASSET} {TF_LABEL} COMPLETE — {h:02d}:{m:02d}:{s:02d}", "OK")
    log("=" * 70)

    if dest.exists():
        with open(dest) as f:
            d = json.load(f)
        v = d["validation"]
        log(f"Phase A PF: {v['phase_a_pf']}")
        log(f"Phase B PF: {v['phase_b_pf']}")
        log(f"Robustness: {v['final_robustness']:.4f}")


if __name__ == "__main__":
    main()
