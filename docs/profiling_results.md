# VEC+POOL Profiling Results

Date: 2026-04-25

## Scope

This pass implemented the TANK VEC+POOL import surface requested by
`TANK_VEC_POOL_IMPLEMENTATION_PLAN.md` and inspected the current codebase before
changing strategy behavior.

## Findings

- `COMB_001_TREND_V1_vectorized.py` already exists and vectorizes ATR, hour,
  weekday, volatility masks, and aggregate result math while preserving the
  sequential trade lifecycle loop.
- `COMB_002_IMPULSE_V2_adaptive.py` already routes ATR through
  `vec_mogalef_core.atr_sma` when available and keeps adaptive target/trade
  lifecycle logic sequential.
- The five POOL phase scripts already centralize multiprocessing and import the
  canonical strategy module names at top level.

## Implementation Decision

Instead of duplicating phase code or mutating validated canonical files, the
implementation adds stable `*_vec_optimized.py` strategy entrypoints and a small
runner that injects those optimized modules before executing the existing POOL
phase scripts. This keeps current BO/TANK scripts untouched and makes rollback
straightforward.

## Profiling Status

Full dataset profiling was not run locally in this implementation pass because
the local checkout does not include the prepared `*_full_*.csv` files under
`new_data`. The added benchmark scripts are ready to run on BO/TANK where those
datasets exist:

```bash
python3 test_vec_opt_single_combo.py
python3 test_vec_opt_pool_100combos.py
```

