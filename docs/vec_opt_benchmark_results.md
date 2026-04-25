# VEC+POOL Benchmark Results

Date: 2026-04-25

## Implemented Artifacts

- `mgf-control/COMB_001_TREND_V1_vec_optimized.py`
- `mgf-control/COMB_002_IMPULSE_V2_vec_optimized.py`
- `mgf-control/vec_opt_phase_runner.py`
- `mgf-control/phase1_signal_independent_pool_vec_opt.py`
- `mgf-control/phase2a_horaire_independent_pool_vec_opt.py`
- `mgf-control/phase2b_regime_independent_pool_vec_opt.py`
- `mgf-control/phase3_exits_independent_pool_vec_opt.py`
- `mgf-control/phase4_stops_independent_pool_vec_opt.py`
- `mgf-control/phase5_combine_filters_vec_opt.py`
- `mgf-control/run_phases_1_to_5_tank_VEC_POOL_OPTIMIZED.sh`
- `mgf-control/test_vec_optimized_equivalence.py`
- `mgf-control/test_vec_opt_single_combo.py`
- `mgf-control/test_vec_opt_pool_100combos.py`

## Validation Commands

Run from `mgf-control`:

```bash
python3 test_vec_optimized_equivalence.py
python3 test_vec_opt_single_combo.py
python3 test_vec_opt_pool_100combos.py
python3 phase1_signal_independent_pool_vec_opt.py --help
python3 phase5_combine_filters_vec_opt.py --help
```

## Deployment Command

On TANK, after syncing the branch:

```bash
cd ~/mogalef-systems-lab/mgf-control
nohup bash run_phases_1_to_5_tank_VEC_POOL_OPTIMIZED.sh > tank_vec_opt_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

Tunable environment variables:

```bash
WORKERS=6 MAX_PARALLEL=2 bash run_phases_1_to_5_tank_VEC_POOL_OPTIMIZED.sh
```

## Notes

- BO/TANK canonical phase scripts remain untouched.
- The optimized phase scripts reuse existing POOL logic but swap strategy
  implementations through `vec_opt_phase_runner.py`.
- Full benchmark timings should be recorded on TANK because that host has the
  prepared `new_data/*_full_*.csv` datasets and target CPU topology.

