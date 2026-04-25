"""
COMB_002_IMPULSE Phase 5 — Cross-Validation Pool Runner

Metodología:
  1. Re-optimiza cada fase EN CRUDO (independiente, sin bloquear fases anteriores).
  2. Extrae Top-3 de cada fase (filtro: min trades + mejor robustness).
  3. Construye grid cruzado: 3^5 = 243 combinaciones.
  4. Evalúa las 243 cross-combos en Phase A + Phase B.
  5. Compara cross-winner vs sequential master (Phase 1-4 secuencial).

Salida:
  COMB002_phase5_{asset}_{tf}_raw_ph1_log.csv
  COMB002_phase5_{asset}_{tf}_raw_ph2a_log.csv
  COMB002_phase5_{asset}_{tf}_raw_ph2b_log.csv
  COMB002_phase5_{asset}_{tf}_raw_ph3_log.csv
  COMB002_phase5_{asset}_{tf}_raw_ph4_log.csv
  COMB002_phase5_{asset}_{tf}_cross_log.csv
  COMB002_phase5_{asset}_{tf}_best_params.json   ← cross-winner final
  COMB002_phase5_{asset}_{tf}_comparison.json    ← cross vs sequential

Uso:
  python3 phase5_COMB002_cross_validation_pool_runner.py --asset ES --timeframe 5m
  python3 phase5_COMB002_cross_validation_pool_runner.py --asset YM --timeframe 10m --workers 8
"""

import argparse
import csv
import json
import subprocess
import sys
from datetime import date
from itertools import product
from multiprocessing import Pool, cpu_count
from pathlib import Path

_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from COMB_002_IMPULSE_V1 import Comb002ImpulseStrategy, Comb002ImpulseParams, load_ohlc_csv

# ── Constants ─────────────────────────────────────────────────────────────────
SUPPORTED_ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
SUPPORTED_TIMEFRAMES = ["5m", "10m", "15m"]
ROBUSTNESS_THRESHOLD = 0.80
MIN_TRADES_A         = 20   # Phase 1 raw uses 20 (same as phase1_pool_runner)
MIN_TRADES           = 30   # Phases 2-5
TOP_N                = 3    # Top-N per phase for cross grid

# ── Raw Phase Grids (mismo que runners originales) ────────────────────────────
# Phase 1 — Signal
SMOOTH_H_RANGE   = [1, 2, 3, 4, 5]
SMOOTH_B_RANGE   = [1, 2, 3, 4, 5]
DISTANCE_H_RANGE = [25, 75, 125, 175, 200]
DISTANCE_L_RANGE = [25, 75, 125, 175, 200]

# Phase 2a — Horaire
HORAIRE_PROFILES = [
    {"id": 1,  "label": "24h_no_filter",         "hours": list(range(0, 24))},
    {"id": 2,  "label": "US_regular_9_15",        "hours": list(range(9, 16))},
    {"id": 3,  "label": "US_extended_9_17",       "hours": list(range(9, 18))},
    {"id": 4,  "label": "US_premarket_8_16",      "hours": list(range(8, 17))},
    {"id": 5,  "label": "NY_morning_9_12",        "hours": list(range(9, 13))},
    {"id": 6,  "label": "NY_afternoon_12_16",     "hours": list(range(12, 17))},
    {"id": 7,  "label": "Mogalef_V1_CET_8_16",   "hours": list(range(8, 17))},
    {"id": 8,  "label": "Mogalef_V1_CEST_7_15",  "hours": list(range(7, 16))},
    {"id": 9,  "label": "Mogalef_V2_CET_19_21",  "hours": [19, 20, 21]},
    {"id": 10, "label": "Mogalef_V2_CEST_18_20", "hours": [18, 19, 20]},
    {"id": 11, "label": "Mogalef_BOTH_CET",      "hours": list(range(8, 17)) + [19, 20, 21]},
    {"id": 12, "label": "Mogalef_BOTH_CEST",     "hours": list(range(7, 16)) + [18, 19, 20]},
]

# Phase 2b — Volatility
VOLATILITY_PROFILES = [
    {"id": 1, "label": "no_filter_0_500",     "atr_min": 0.0,  "atr_max": 500.0},
    {"id": 2, "label": "min_floor_10_500",    "atr_min": 10.0, "atr_max": 500.0},
    {"id": 3, "label": "max_ceiling_0_200",   "atr_min": 0.0,  "atr_max": 200.0},
    {"id": 4, "label": "tight_band_10_250",   "atr_min": 10.0, "atr_max": 250.0},
    {"id": 5, "label": "selective_20_200",    "atr_min": 20.0, "atr_max": 200.0},
]

# Phase 3 — Exits
SCALPING_COEF_RANGE = [1.5, 2.0, 3.0, 4.0, 5.0]
TIMESCAN_RANGE      = [10, 12, 15, 18, 20]

# Phase 4 — Stops
SUPERSTOP_QUALITY_RANGE = [1, 2, 3]
SUPERSTOP_COEF_RANGE    = [2.0, 3.0, 4.0, 5.0]

# ── Default values (from Comb002ImpulseParams) ────────────────────────────────
DEFAULT_SIGNAL   = {"stpmt_smooth_h": 2, "stpmt_smooth_b": 2,
                    "stpmt_distance_max_h": 200, "stpmt_distance_max_l": 200}
DEFAULT_HORAIRE  = list(range(9, 16))
DEFAULT_VOLAT    = {"atr_min": 0.0, "atr_max": 500.0}
DEFAULT_EXITS    = {"scalping_target_coef_volat": 3.0, "timescan_bars": 15}
DEFAULT_STOPS    = {"superstop_quality": 2, "superstop_coef_volat": 3.0}


# ── Robustness helper ─────────────────────────────────────────────────────────
def calc_robustness(pf_a: float, pf_b: float) -> float:
    return round(pf_b / pf_a, 4) if pf_a > 0 else 0.0


# ════════════════════════════════════════════════════════════════════════════
# RAW PHASE 1 — Signal
# ════════════════════════════════════════════════════════════════════════════

def _run_raw_ph1(args):
    smooth_h, smooth_b, dist_h, dist_l, phase_a_rows, phase_b_rows = args
    params = Comb002ImpulseParams(
        stpmt_smooth_h=smooth_h,
        stpmt_smooth_b=smooth_b,
        stpmt_distance_max_h=dist_h,
        stpmt_distance_max_l=dist_l,
        horaire_allowed_hours_utc=DEFAULT_HORAIRE,
        volatility_atr_min=DEFAULT_VOLAT["atr_min"],
        volatility_atr_max=DEFAULT_VOLAT["atr_max"],
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        scalping_target_coef_volat=DEFAULT_EXITS["scalping_target_coef_volat"],
        timescan_bars=DEFAULT_EXITS["timescan_bars"],
        superstop_quality=DEFAULT_STOPS["superstop_quality"],
        superstop_coef_volat=DEFAULT_STOPS["superstop_coef_volat"],
    )
    s = Comb002ImpulseStrategy(params)
    ra = s.run(phase_a_rows)
    rb = s.run(phase_b_rows)
    return {
        "stpmt_smooth_h": smooth_h, "stpmt_smooth_b": smooth_b,
        "stpmt_distance_max_h": dist_h, "stpmt_distance_max_l": dist_l,
        "phase_a_pf": round(ra.profit_factor, 4), "phase_a_trades": len(ra.trades),
        "phase_b_pf": round(rb.profit_factor, 4), "phase_b_trades": len(rb.trades),
        "robustness": calc_robustness(ra.profit_factor, rb.profit_factor),
    }


def run_raw_phase1(phase_a_rows, phase_b_rows, workers: int, asset: str, tf: str):
    combos = [(sh, sb, dh, dl, phase_a_rows, phase_b_rows)
              for sh, sb, dh, dl in product(SMOOTH_H_RANGE, SMOOTH_B_RANGE,
                                             DISTANCE_H_RANGE, DISTANCE_L_RANGE)]
    total = len(combos)
    print(f"\n  [PH1-RAW] {total} combos...")
    results = []
    with Pool(processes=workers) as pool:
        for row in pool.imap_unordered(_run_raw_ph1, combos, chunksize=10):
            results.append(row)
    results.sort(key=lambda x: x["robustness"], reverse=True)

    log_file = f"COMB002_phase5_{asset}_{tf}_raw_ph1_log.csv"
    fields = ["stpmt_smooth_h", "stpmt_smooth_b", "stpmt_distance_max_h",
              "stpmt_distance_max_l", "phase_a_pf", "phase_a_trades",
              "phase_b_pf", "phase_b_trades", "robustness"]
    with open(log_file, "w", newline="") as fh:
        csv.DictWriter(fh, fieldnames=fields).writeheader()
        csv.DictWriter(fh, fieldnames=fields).writerows(results)
    print(f"  [OK] {log_file}")

    valid = [r for r in results if r["phase_a_trades"] >= MIN_TRADES_A]
    top = (valid if valid else results)[:TOP_N]
    print(f"  Top-{TOP_N} PH1: " + " | ".join(
        f"sh={r['stpmt_smooth_h']} sb={r['stpmt_smooth_b']} dh={r['stpmt_distance_max_h']} "
        f"dl={r['stpmt_distance_max_l']} Rob={r['robustness']:.4f}" for r in top))
    return top


# ════════════════════════════════════════════════════════════════════════════
# RAW PHASE 2a — Horaire
# ════════════════════════════════════════════════════════════════════════════

def _run_raw_ph2a(args):
    profile, phase_a_rows, phase_b_rows = args
    params = Comb002ImpulseParams(
        stpmt_smooth_h=DEFAULT_SIGNAL["stpmt_smooth_h"],
        stpmt_smooth_b=DEFAULT_SIGNAL["stpmt_smooth_b"],
        stpmt_distance_max_h=DEFAULT_SIGNAL["stpmt_distance_max_h"],
        stpmt_distance_max_l=DEFAULT_SIGNAL["stpmt_distance_max_l"],
        horaire_allowed_hours_utc=profile["hours"],
        volatility_atr_min=DEFAULT_VOLAT["atr_min"],
        volatility_atr_max=DEFAULT_VOLAT["atr_max"],
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        scalping_target_coef_volat=DEFAULT_EXITS["scalping_target_coef_volat"],
        timescan_bars=DEFAULT_EXITS["timescan_bars"],
        superstop_quality=DEFAULT_STOPS["superstop_quality"],
        superstop_coef_volat=DEFAULT_STOPS["superstop_coef_volat"],
    )
    s = Comb002ImpulseStrategy(params)
    ra = s.run(phase_a_rows)
    rb = s.run(phase_b_rows)
    return {
        "profile_id": profile["id"], "horaire_label": profile["label"],
        "horaire_allowed_hours_utc": profile["hours"],
        "phase_a_pf": round(ra.profit_factor, 4), "phase_a_trades": len(ra.trades),
        "phase_b_pf": round(rb.profit_factor, 4), "phase_b_trades": len(rb.trades),
        "robustness": calc_robustness(ra.profit_factor, rb.profit_factor),
    }


def run_raw_phase2a(phase_a_rows, phase_b_rows, workers: int, asset: str, tf: str):
    combos = [(p, phase_a_rows, phase_b_rows) for p in HORAIRE_PROFILES]
    print(f"\n  [PH2a-RAW] {len(combos)} profiles...")
    results = []
    with Pool(processes=min(workers, len(HORAIRE_PROFILES))) as pool:
        for row in pool.imap_unordered(_run_raw_ph2a, combos, chunksize=1):
            results.append(row)
    results.sort(key=lambda x: x["robustness"], reverse=True)

    log_file = f"COMB002_phase5_{asset}_{tf}_raw_ph2a_log.csv"
    fields = ["profile_id", "horaire_label", "phase_a_pf", "phase_a_trades",
              "phase_b_pf", "phase_b_trades", "robustness"]
    with open(log_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    print(f"  [OK] {log_file}")

    valid = [r for r in results if r["phase_a_trades"] >= MIN_TRADES]
    top = (valid if valid else results)[:TOP_N]
    print(f"  Top-{TOP_N} PH2a: " + " | ".join(
        f"{r['horaire_label']} Rob={r['robustness']:.4f}" for r in top))
    return top


# ════════════════════════════════════════════════════════════════════════════
# RAW PHASE 2b — Volatility
# ════════════════════════════════════════════════════════════════════════════

def _run_raw_ph2b(args):
    profile, phase_a_rows, phase_b_rows = args
    params = Comb002ImpulseParams(
        stpmt_smooth_h=DEFAULT_SIGNAL["stpmt_smooth_h"],
        stpmt_smooth_b=DEFAULT_SIGNAL["stpmt_smooth_b"],
        stpmt_distance_max_h=DEFAULT_SIGNAL["stpmt_distance_max_h"],
        stpmt_distance_max_l=DEFAULT_SIGNAL["stpmt_distance_max_l"],
        horaire_allowed_hours_utc=DEFAULT_HORAIRE,
        volatility_atr_min=profile["atr_min"],
        volatility_atr_max=profile["atr_max"],
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        scalping_target_coef_volat=DEFAULT_EXITS["scalping_target_coef_volat"],
        timescan_bars=DEFAULT_EXITS["timescan_bars"],
        superstop_quality=DEFAULT_STOPS["superstop_quality"],
        superstop_coef_volat=DEFAULT_STOPS["superstop_coef_volat"],
    )
    s = Comb002ImpulseStrategy(params)
    ra = s.run(phase_a_rows)
    rb = s.run(phase_b_rows)
    return {
        "profile_id": profile["id"], "volatility_label": profile["label"],
        "volatility_atr_min": profile["atr_min"], "volatility_atr_max": profile["atr_max"],
        "phase_a_pf": round(ra.profit_factor, 4), "phase_a_trades": len(ra.trades),
        "phase_b_pf": round(rb.profit_factor, 4), "phase_b_trades": len(rb.trades),
        "robustness": calc_robustness(ra.profit_factor, rb.profit_factor),
    }


def run_raw_phase2b(phase_a_rows, phase_b_rows, workers: int, asset: str, tf: str):
    combos = [(p, phase_a_rows, phase_b_rows) for p in VOLATILITY_PROFILES]
    print(f"\n  [PH2b-RAW] {len(combos)} profiles...")
    results = []
    with Pool(processes=min(workers, len(VOLATILITY_PROFILES))) as pool:
        for row in pool.imap_unordered(_run_raw_ph2b, combos, chunksize=1):
            results.append(row)
    results.sort(key=lambda x: x["robustness"], reverse=True)

    log_file = f"COMB002_phase5_{asset}_{tf}_raw_ph2b_log.csv"
    fields = ["profile_id", "volatility_label", "volatility_atr_min", "volatility_atr_max",
              "phase_a_pf", "phase_a_trades", "phase_b_pf", "phase_b_trades", "robustness"]
    with open(log_file, "w", newline="") as fh:
        csv.DictWriter(fh, fieldnames=fields).writeheader()
        csv.DictWriter(fh, fieldnames=fields).writerows(results)
    print(f"  [OK] {log_file}")

    valid = [r for r in results if r["phase_a_trades"] >= MIN_TRADES]
    top = (valid if valid else results)[:TOP_N]
    print(f"  Top-{TOP_N} PH2b: " + " | ".join(
        f"{r['volatility_label']} Rob={r['robustness']:.4f}" for r in top))
    return top


# ════════════════════════════════════════════════════════════════════════════
# RAW PHASE 3 — Exits
# ════════════════════════════════════════════════════════════════════════════

def _run_raw_ph3(args):
    scalp_coef, timescan, phase_a_rows, phase_b_rows = args
    params = Comb002ImpulseParams(
        stpmt_smooth_h=DEFAULT_SIGNAL["stpmt_smooth_h"],
        stpmt_smooth_b=DEFAULT_SIGNAL["stpmt_smooth_b"],
        stpmt_distance_max_h=DEFAULT_SIGNAL["stpmt_distance_max_h"],
        stpmt_distance_max_l=DEFAULT_SIGNAL["stpmt_distance_max_l"],
        horaire_allowed_hours_utc=DEFAULT_HORAIRE,
        volatility_atr_min=DEFAULT_VOLAT["atr_min"],
        volatility_atr_max=DEFAULT_VOLAT["atr_max"],
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        scalping_target_coef_volat=scalp_coef,
        timescan_bars=timescan,
        superstop_quality=DEFAULT_STOPS["superstop_quality"],
        superstop_coef_volat=DEFAULT_STOPS["superstop_coef_volat"],
    )
    s = Comb002ImpulseStrategy(params)
    ra = s.run(phase_a_rows)
    rb = s.run(phase_b_rows)
    return {
        "scalping_target_coef_volat": scalp_coef, "timescan_bars": timescan,
        "phase_a_pf": round(ra.profit_factor, 4), "phase_a_trades": len(ra.trades),
        "phase_b_pf": round(rb.profit_factor, 4), "phase_b_trades": len(rb.trades),
        "robustness": calc_robustness(ra.profit_factor, rb.profit_factor),
    }


def run_raw_phase3(phase_a_rows, phase_b_rows, workers: int, asset: str, tf: str):
    combos = [(sc, ts, phase_a_rows, phase_b_rows)
              for sc, ts in product(SCALPING_COEF_RANGE, TIMESCAN_RANGE)]
    print(f"\n  [PH3-RAW] {len(combos)} combos...")
    results = []
    with Pool(processes=workers) as pool:
        for row in pool.imap_unordered(_run_raw_ph3, combos, chunksize=5):
            results.append(row)
    results.sort(key=lambda x: x["robustness"], reverse=True)

    log_file = f"COMB002_phase5_{asset}_{tf}_raw_ph3_log.csv"
    fields = ["scalping_target_coef_volat", "timescan_bars",
              "phase_a_pf", "phase_a_trades", "phase_b_pf", "phase_b_trades", "robustness"]
    with open(log_file, "w", newline="") as fh:
        csv.DictWriter(fh, fieldnames=fields).writeheader()
        csv.DictWriter(fh, fieldnames=fields).writerows(results)
    print(f"  [OK] {log_file}")

    valid = [r for r in results if r["phase_a_trades"] >= MIN_TRADES]
    top = (valid if valid else results)[:TOP_N]
    print(f"  Top-{TOP_N} PH3: " + " | ".join(
        f"coef={r['scalping_target_coef_volat']} ts={r['timescan_bars']} Rob={r['robustness']:.4f}"
        for r in top))
    return top


# ════════════════════════════════════════════════════════════════════════════
# RAW PHASE 4 — Stops
# ════════════════════════════════════════════════════════════════════════════

def _run_raw_ph4(args):
    quality, coef, phase_a_rows, phase_b_rows = args
    params = Comb002ImpulseParams(
        stpmt_smooth_h=DEFAULT_SIGNAL["stpmt_smooth_h"],
        stpmt_smooth_b=DEFAULT_SIGNAL["stpmt_smooth_b"],
        stpmt_distance_max_h=DEFAULT_SIGNAL["stpmt_distance_max_h"],
        stpmt_distance_max_l=DEFAULT_SIGNAL["stpmt_distance_max_l"],
        horaire_allowed_hours_utc=DEFAULT_HORAIRE,
        volatility_atr_min=DEFAULT_VOLAT["atr_min"],
        volatility_atr_max=DEFAULT_VOLAT["atr_max"],
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        scalping_target_coef_volat=DEFAULT_EXITS["scalping_target_coef_volat"],
        timescan_bars=DEFAULT_EXITS["timescan_bars"],
        superstop_quality=quality,
        superstop_coef_volat=coef,
    )
    s = Comb002ImpulseStrategy(params)
    ra = s.run(phase_a_rows)
    rb = s.run(phase_b_rows)
    return {
        "superstop_quality": quality, "superstop_coef_volat": coef,
        "phase_a_pf": round(ra.profit_factor, 4), "phase_a_trades": len(ra.trades),
        "phase_b_pf": round(rb.profit_factor, 4), "phase_b_trades": len(rb.trades),
        "robustness": calc_robustness(ra.profit_factor, rb.profit_factor),
    }


def run_raw_phase4(phase_a_rows, phase_b_rows, workers: int, asset: str, tf: str):
    combos = [(q, c, phase_a_rows, phase_b_rows)
              for q, c in product(SUPERSTOP_QUALITY_RANGE, SUPERSTOP_COEF_RANGE)]
    print(f"\n  [PH4-RAW] {len(combos)} combos...")
    results = []
    with Pool(processes=workers) as pool:
        for row in pool.imap_unordered(_run_raw_ph4, combos, chunksize=4):
            results.append(row)
    results.sort(key=lambda x: x["robustness"], reverse=True)

    log_file = f"COMB002_phase5_{asset}_{tf}_raw_ph4_log.csv"
    fields = ["superstop_quality", "superstop_coef_volat",
              "phase_a_pf", "phase_a_trades", "phase_b_pf", "phase_b_trades", "robustness"]
    with open(log_file, "w", newline="") as fh:
        csv.DictWriter(fh, fieldnames=fields).writeheader()
        csv.DictWriter(fh, fieldnames=fields).writerows(results)
    print(f"  [OK] {log_file}")

    valid = [r for r in results if r["phase_a_trades"] >= MIN_TRADES]
    top = (valid if valid else results)[:TOP_N]
    print(f"  Top-{TOP_N} PH4: " + " | ".join(
        f"q={r['superstop_quality']} coef={r['superstop_coef_volat']} Rob={r['robustness']:.4f}"
        for r in top))
    return top


# ════════════════════════════════════════════════════════════════════════════
# CROSS GRID — 3^5 = 243 combos
# ════════════════════════════════════════════════════════════════════════════

def _run_cross_combo(args):
    (ph1, ph2a, ph2b, ph3, ph4, phase_a_rows, phase_b_rows) = args
    params = Comb002ImpulseParams(
        stpmt_smooth_h=ph1["stpmt_smooth_h"],
        stpmt_smooth_b=ph1["stpmt_smooth_b"],
        stpmt_distance_max_h=ph1["stpmt_distance_max_h"],
        stpmt_distance_max_l=ph1["stpmt_distance_max_l"],
        horaire_allowed_hours_utc=ph2a["horaire_allowed_hours_utc"],
        volatility_atr_min=ph2b["volatility_atr_min"],
        volatility_atr_max=ph2b["volatility_atr_max"],
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        scalping_target_coef_volat=ph3["scalping_target_coef_volat"],
        timescan_bars=ph3["timescan_bars"],
        superstop_quality=ph4["superstop_quality"],
        superstop_coef_volat=ph4["superstop_coef_volat"],
    )
    s = Comb002ImpulseStrategy(params)
    ra = s.run(phase_a_rows)
    rb = s.run(phase_b_rows)
    rob = calc_robustness(ra.profit_factor, rb.profit_factor)
    return {
        # Signal
        "stpmt_smooth_h":           ph1["stpmt_smooth_h"],
        "stpmt_smooth_b":           ph1["stpmt_smooth_b"],
        "stpmt_distance_max_h":     ph1["stpmt_distance_max_h"],
        "stpmt_distance_max_l":     ph1["stpmt_distance_max_l"],
        # Horaire
        "horaire_label":            ph2a["horaire_label"],
        # Volatility
        "volatility_label":         ph2b["volatility_label"],
        "volatility_atr_min":       ph2b["volatility_atr_min"],
        "volatility_atr_max":       ph2b["volatility_atr_max"],
        # Exits
        "scalping_target_coef_volat": ph3["scalping_target_coef_volat"],
        "timescan_bars":            ph3["timescan_bars"],
        # Stops
        "superstop_quality":        ph4["superstop_quality"],
        "superstop_coef_volat":     ph4["superstop_coef_volat"],
        # Results
        "phase_a_pf":    round(ra.profit_factor, 4),
        "phase_a_wr":    round(ra.win_rate, 4),
        "phase_a_trades": len(ra.trades),
        "phase_a_equity": round(ra.equity_points, 2),
        "phase_b_pf":    round(rb.profit_factor, 4),
        "phase_b_wr":    round(rb.win_rate, 4),
        "phase_b_trades": len(rb.trades),
        "phase_b_equity": round(rb.equity_points, 2),
        "robustness":    rob,
    }


def run_cross_grid(top_ph1, top_ph2a, top_ph2b, top_ph3, top_ph4,
                   phase_a_rows, phase_b_rows, workers: int, asset: str, tf: str):
    combos = [
        (p1, p2a, p2b, p3, p4, phase_a_rows, phase_b_rows)
        for p1, p2a, p2b, p3, p4 in product(top_ph1, top_ph2a, top_ph2b, top_ph3, top_ph4)
    ]
    total = len(combos)
    print(f"\n  [CROSS] {total} combos ({TOP_N}^5)...")

    results = []
    completed = 0
    best_rob = 0.0

    with Pool(processes=workers) as pool:
        for row in pool.imap_unordered(_run_cross_combo, combos, chunksize=5):
            results.append(row)
            completed += 1
            if row["robustness"] > best_rob:
                best_rob = row["robustness"]
                flag = ">>> PASS <<<" if best_rob >= ROBUSTNESS_THRESHOLD else ""
                print(f"  [{completed:>3}/{total}] NEW BEST {flag}: "
                      f"Rob={best_rob:.4f} | PF_A={row['phase_a_pf']:.3f} "
                      f"PF_B={row['phase_b_pf']:.3f} | T_A={row['phase_a_trades']}")
                sys.stdout.flush()

    # Sort: valid trades first, then by robustness
    valid   = [r for r in results if r["phase_a_trades"] >= MIN_TRADES
               and r["phase_b_trades"] >= MIN_TRADES // 2]
    invalid = [r for r in results if r not in valid]
    valid.sort(key=lambda x: x["robustness"], reverse=True)
    invalid.sort(key=lambda x: x["robustness"], reverse=True)
    results = valid + invalid

    log_file = f"COMB002_phase5_{asset}_{tf}_cross_log.csv"
    fields = ["stpmt_smooth_h", "stpmt_smooth_b", "stpmt_distance_max_h", "stpmt_distance_max_l",
              "horaire_label", "volatility_label", "volatility_atr_min", "volatility_atr_max",
              "scalping_target_coef_volat", "timescan_bars",
              "superstop_quality", "superstop_coef_volat",
              "phase_a_pf", "phase_a_wr", "phase_a_trades", "phase_a_equity",
              "phase_b_pf", "phase_b_wr", "phase_b_trades", "phase_b_equity",
              "robustness"]
    with open(log_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    print(f"  [OK] {log_file}")

    return results


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="COMB_002 IMPULSE Phase 5 — Cross-Validation Pool Runner"
    )
    parser.add_argument("--asset",     required=True, choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True, choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument("--workers",   type=int, default=None)
    args = parser.parse_args()

    asset     = args.asset
    tf        = args.timeframe
    workers   = args.workers or cpu_count()
    opt_date  = date.today().strftime("%Y%m%d")
    opt_id    = f"OPT-COMB002-{asset}-{tf}-PH5-{opt_date}"

    print(f"\n{'='*80}")
    print(f"COMB_002_IMPULSE | Phase 5 Cross-Validation | {asset} {tf}")
    print(f"Optimization ID: {opt_id}")
    print(f"{'='*80}")
    print(f"Workers: {workers} | Top-N per phase: {TOP_N} | Cross combos: {TOP_N}^5 = {TOP_N**5}")

    # ── Load data ──────────────────────────────────────────────────────────
    phase_a_file = f"{asset}_phase_A_{tf}.csv"
    phase_b_file = f"{asset}_phase_B_{tf}.csv"
    for f in [phase_a_file, phase_b_file]:
        if not Path(f).exists():
            print(f"[ERROR] {f} not found.")
            sys.exit(1)

    phase_a_rows = load_ohlc_csv(phase_a_file)
    phase_b_rows = load_ohlc_csv(phase_b_file)
    print(f"Phase A: {len(phase_a_rows):,} bars | Phase B: {len(phase_b_rows):,} bars")

    # ── Load sequential master (optional, for comparison) ─────────────────
    seq_master_file = "COMB002_MASTER_PARAMS_SEQUENTIAL.json"
    seq_params = None
    if Path(seq_master_file).exists():
        with open(seq_master_file) as fh:
            master = json.load(fh)
        key = f"{asset}_{tf}"
        seq_params = master.get("by_asset_tf", {}).get(key)
        if seq_params:
            print(f"Sequential master loaded: {key} Rob={seq_params['final_robustness']:.4f}")
        else:
            print(f"[WARN] {key} not found in {seq_master_file} — no comparison possible")
    else:
        print(f"[WARN] {seq_master_file} not found — no comparison possible")

    # ── Step 1: Raw phase optimizations ───────────────────────────────────
    print(f"\n{'─'*60}")
    print("STEP 1 — Raw phase optimizations (each phase with defaults elsewhere)")
    print(f"{'─'*60}")

    top_ph1  = run_raw_phase1(phase_a_rows, phase_b_rows, workers, asset, tf)
    top_ph2a = run_raw_phase2a(phase_a_rows, phase_b_rows, workers, asset, tf)
    top_ph2b = run_raw_phase2b(phase_a_rows, phase_b_rows, workers, asset, tf)
    top_ph3  = run_raw_phase3(phase_a_rows, phase_b_rows, workers, asset, tf)
    top_ph4  = run_raw_phase4(phase_a_rows, phase_b_rows, workers, asset, tf)

    # ── Step 2: Cross grid ─────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("STEP 2 — Cross grid (3^5 = 243 combinations of top-N winners)")
    print(f"{'─'*60}")

    cross_results = run_cross_grid(
        top_ph1, top_ph2a, top_ph2b, top_ph3, top_ph4,
        phase_a_rows, phase_b_rows, workers, asset, tf
    )

    # ── Step 3: Cross winner ───────────────────────────────────────────────
    cross_winner = cross_results[0]

    best_params = {
        "optimization_id":           opt_id,
        "strategy":                  "COMB_002_IMPULSE",
        "asset":                     asset,
        "timeframe":                 tf,
        "phase":                     "5_cross",
        "approach":                  "cross_validation",
        "optimization_date":         date.today().strftime("%Y-%m-%d"),
        # Signal
        "stpmt_smooth_h":            cross_winner["stpmt_smooth_h"],
        "stpmt_smooth_b":            cross_winner["stpmt_smooth_b"],
        "stpmt_distance_max_h":      cross_winner["stpmt_distance_max_h"],
        "stpmt_distance_max_l":      cross_winner["stpmt_distance_max_l"],
        # Horaire
        "horaire_label":             cross_winner["horaire_label"],
        # Volatility
        "volatility_label":          cross_winner["volatility_label"],
        "volatility_atr_min":        cross_winner["volatility_atr_min"],
        "volatility_atr_max":        cross_winner["volatility_atr_max"],
        # Exits
        "scalping_target_coef_volat": cross_winner["scalping_target_coef_volat"],
        "timescan_bars":             cross_winner["timescan_bars"],
        # Stops
        "superstop_quality":         cross_winner["superstop_quality"],
        "superstop_coef_volat":      cross_winner["superstop_coef_volat"],
        # Results
        "robustness":                cross_winner["robustness"],
        "phase_a_pf":                cross_winner["phase_a_pf"],
        "phase_b_pf":                cross_winner["phase_b_pf"],
        "phase_a_trades":            cross_winner["phase_a_trades"],
        "phase_b_trades":            cross_winner["phase_b_trades"],
        "robustness_pass":           cross_winner["robustness"] >= ROBUSTNESS_THRESHOLD,
        "min_trades_pass":           cross_winner["phase_a_trades"] >= MIN_TRADES,
    }

    best_file = f"COMB002_phase5_{asset}_{tf}_best_params.json"
    with open(best_file, "w") as fh:
        json.dump(best_params, fh, indent=2)
    print(f"\n  [OK] {best_file}")

    # ── Step 4: Compare cross vs sequential ───────────────────────────────
    comparison = {
        "optimization_id": opt_id,
        "asset": asset,
        "timeframe": tf,
        "cross_winner": {
            "robustness":    cross_winner["robustness"],
            "phase_a_pf":    cross_winner["phase_a_pf"],
            "phase_b_pf":    cross_winner["phase_b_pf"],
            "phase_a_trades": cross_winner["phase_a_trades"],
            "robustness_pass": cross_winner["robustness"] >= ROBUSTNESS_THRESHOLD,
        },
        "sequential_master": None,
        "verdict": None,
        "delta_robustness": None,
    }

    if seq_params:
        seq_rob  = seq_params.get("final_robustness", 0.0)
        seq_pf_a = seq_params.get("final_phase_a_pf", 0.0)
        seq_pf_b = seq_params.get("final_phase_b_pf", 0.0)
        seq_trades = seq_params.get("final_phase_a_trades", 0)

        delta = round(cross_winner["robustness"] - seq_rob, 4)

        comparison["sequential_master"] = {
            "robustness":    seq_rob,
            "phase_a_pf":    seq_pf_a,
            "phase_b_pf":    seq_pf_b,
            "phase_a_trades": seq_trades,
            "robustness_pass": seq_rob >= ROBUSTNESS_THRESHOLD,
        }
        comparison["delta_robustness"] = delta

        if abs(delta) < 0.02:
            verdict = "EQUIVALENT — both approaches converge (delta < 0.02)"
        elif delta > 0:
            verdict = f"CROSS WINS — cross robustness +{delta:.4f} better than sequential"
        else:
            verdict = f"SEQUENTIAL WINS — sequential robustness {abs(delta):.4f} better than cross"

        comparison["verdict"] = verdict
        comparison["recommended_params"] = (
            "cross" if delta >= 0 else "sequential"
        )

    comp_file = f"COMB002_phase5_{asset}_{tf}_comparison.json"
    with open(comp_file, "w") as fh:
        json.dump(comparison, fh, indent=2)
    print(f"  [OK] {comp_file}")

    # ── Final summary ──────────────────────────────────────────────────────
    cross_status = ">>> PASS <<<" if cross_winner["robustness"] >= ROBUSTNESS_THRESHOLD else "!!! FAIL !!!"

    print(f"\n{'='*80}")
    print(f"PHASE 5 DONE: {asset} {tf}")
    print(f"  Optimization ID: {opt_id}")
    print(f"\n  CROSS WINNER [{cross_status}]:")
    print(f"    Signal:     sh={cross_winner['stpmt_smooth_h']} sb={cross_winner['stpmt_smooth_b']} "
          f"dh={cross_winner['stpmt_distance_max_h']} dl={cross_winner['stpmt_distance_max_l']}")
    print(f"    Horaire:    {cross_winner['horaire_label']}")
    print(f"    Volatility: {cross_winner['volatility_label']} "
          f"({cross_winner['volatility_atr_min']}-{cross_winner['volatility_atr_max']})")
    print(f"    Exits:      coef={cross_winner['scalping_target_coef_volat']} "
          f"timescan={cross_winner['timescan_bars']}")
    print(f"    Stops:      quality={cross_winner['superstop_quality']} "
          f"coef={cross_winner['superstop_coef_volat']}")
    print(f"    Robustness: {cross_winner['robustness']:.4f}")
    print(f"    PF_A/PF_B:  {cross_winner['phase_a_pf']:.4f} / {cross_winner['phase_b_pf']:.4f}")
    print(f"    Trades A/B: {cross_winner['phase_a_trades']} / {cross_winner['phase_b_trades']}")

    if seq_params and comparison["verdict"]:
        print(f"\n  COMPARISON vs SEQUENTIAL:")
        print(f"    {comparison['verdict']}")
        print(f"    Cross Rob={cross_winner['robustness']:.4f} | "
              f"Sequential Rob={comparison['sequential_master']['robustness']:.4f}")
        print(f"    → USE: {comparison['recommended_params'].upper()} params")

    print(f"\n  Files written:")
    print(f"    {best_file}")
    print(f"    {comp_file}")
    print(f"    COMB002_phase5_{asset}_{tf}_cross_log.csv")
    print(f"{'='*80}\n")

    print("NEXT STEP: Consolidate final winner (cross vs sequential) into")
    print("  COMB002_FINAL_PARAMS.json using consolidate_COMB002_final_winner.py")

    # ── Git push results ───────────────────────────────────────────────────
    try:
        repo_root = Path(__file__).resolve().parents[1]
        files_to_add = [
            f"mgf-control/COMB002_phase5_{asset}_{tf}_best_params.json",
            f"mgf-control/COMB002_phase5_{asset}_{tf}_comparison.json",
        ]
        subprocess.run(["git", "add"] + files_to_add, cwd=repo_root, check=True)
        rob_str = f"{cross_winner['robustness']:.4f}"
        status_str = "PASS" if cross_winner["robustness"] >= ROBUSTNESS_THRESHOLD else "FAIL"
        msg = (f"PH5 DONE - {asset} {tf} | {opt_id} | "
               f"Rob={rob_str} {status_str} | "
               f"PF_B={cross_winner['phase_b_pf']:.4f}")
        subprocess.run(["git", "commit", "-m", msg], cwd=repo_root, check=True)
        subprocess.run(["git", "push"], cwd=repo_root, check=True)
        print(f"\n[GIT] Pushed: {msg}")
    except subprocess.CalledProcessError as e:
        print(f"\n[GIT WARNING] Push failed: {e} — results saved locally")


if __name__ == "__main__":
    main()
