#!/usr/bin/env python3
"""Quick test: COMB_001 Phase 1 with fixed parameter names."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ("mgf-divergence-lab", "mgf-regime-filter-lab", "mgf-stop-lab"):
    p = str(ROOT / sub / "src")
    if p not in sys.path:
        sys.path.append(p)
sys.path.append(str(Path(__file__).resolve().parent))

from COMB_001_TREND_V1 import Comb001TrendStrategy, Comb001TrendParams
from COMB_002_IMPULSE_V2_adaptive import load_ohlc_csv

# Load data
data_path = ROOT / "new_data" / "MNQ_full_15m.csv"
print(f"[TEST] Loading {data_path.name}...")
data = load_ohlc_csv(str(data_path))
print(f"  {len(data):,} rows")

# Test a few signal combos with COMB_001
test_combos = [
    {"smooth_h": 2, "smooth_b": 2, "dist_max_h": 75, "dist_max_l": 75},
    {"smooth_h": 3, "smooth_b": 3, "dist_max_h": 125, "dist_max_l": 125},
    {"smooth_h": 4, "smooth_b": 4, "dist_max_h": 200, "dist_max_l": 200},
]

print("\n[TEST] Running 3 test combos with COMB_001...")
for i, combo in enumerate(test_combos, 1):
    try:
        params = Comb001TrendParams(
            stpmt_smooth_h=combo["smooth_h"],
            stpmt_smooth_b=combo["smooth_b"],
            stpmt_distance_max_h=combo["dist_max_h"],
            stpmt_distance_max_l=combo["dist_max_l"],
            horaire_allowed_hours_utc=list(range(24)),
            trend_enforce_date_kill_switch=False,
        )
        strat = Comb001TrendStrategy(params)
        result = strat.run(data)
        print(f"  [{i}] smooth=({combo['smooth_h']},{combo['smooth_b']}) dist=({combo['dist_max_h']},{combo['dist_max_l']})")
        print(f"      trades={len(result.trades)} PF={result.profit_factor:.3f} WR={result.win_rate:.2%}")
    except Exception as e:
        print(f"  [{i}] ERROR: {e}")

print("\n[TEST] Done.")
