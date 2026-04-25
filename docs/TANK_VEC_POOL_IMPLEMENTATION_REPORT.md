# TANK VEC+POOL Implementation Report

Date: 2026-04-25

## What Was Implemented

Implemented the VEC+POOL deployment surface described in
`docs/TANK_VEC_POOL_IMPLEMENTATION_PLAN.md` without modifying the existing
canonical strategy or phase scripts.

## Strategy Entry Points

- Added `COMB_001_TREND_V1_vec_optimized.py`.
  - Reuses `COMB_001_TREND_V1_vectorized.py`.
  - Exposes `Comb001TrendVecOptimized`.
  - Provides `Comb001TrendStrategy` alias for drop-in phase compatibility.

- Added `COMB_002_IMPULSE_V2_vec_optimized.py`.
  - Reuses `COMB_002_IMPULSE_V2_adaptive.py`.
  - Exposes `Comb002ImpulseV2VecOptimized`.
  - Provides `Comb002ImpulseV2Strategy` alias for drop-in phase compatibility.

## Phase Scripts

Added VEC+POOL wrappers for phases 1-5:

- `phase1_signal_independent_pool_vec_opt.py`
- `phase2a_horaire_independent_pool_vec_opt.py`
- `phase2b_regime_independent_pool_vec_opt.py`
- `phase3_exits_independent_pool_vec_opt.py`
- `phase4_stops_independent_pool_vec_opt.py`
- `phase5_combine_filters_vec_opt.py`

These wrappers run the existing POOL scripts through `vec_opt_phase_runner.py`,
which injects the optimized strategy modules before script execution.

## Orchestrator

Added `run_phases_1_to_5_tank_VEC_POOL_OPTIMIZED.sh`.

Defaults:

- `WORKERS=6`
- `MAX_PARALLEL=2`
- Logs to `mgf-control/logs/tank_VEC_OPT_<ASSET>_<TF>_<COMB>.log`

## Tests Added

- `test_vec_optimized_equivalence.py`
- `test_vec_opt_single_combo.py`
- `test_vec_opt_pool_100combos.py`

## Remaining Work

- Run the benchmark suite on TANK using prepared `new_data/*_full_*.csv`.
- Record actual Phase 1 and end-to-end timing in `docs/vec_opt_benchmark_results.md`.
- If MNQ 15m COMB_001 still returns zero trades under POOL, add worker-level
  traceback capture in the canonical phase scripts.
- No blocked-day/weekday context filter is part of this implementation. Any
  existing weekday attributes remain at neutral defaults and are not used as an
  optimization dimension.
