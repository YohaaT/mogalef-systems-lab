# Phase 2 Scripts - Creation Status

**Date:** 2026-04-22  
**Status:** ✅ COMPLETE - Ready for Execution

---

## Summary

All Phase 2 optimization scripts have been created and are ready to execute. The Phase 2 workflow will:

1. Optimize **Trend Filter** (150 combos across 2 blocks)
2. Optimize **Horaire** (6 sequential UTC hour profiles)
3. Optimize **Volatility** (5 sequential ATR bands)
4. Consolidate all results into final Phase 2 best params

**Total Estimated Runtime:** 20-25 minutes (or 13-15 min on VPS with parallel blocks)

---

## Created Files

### Core Optimization Scripts

| File | Purpose | Type | Status |
|------|---------|------|--------|
| `phase2a_trend_optimization_block_runner_vec.py` | Trend Filter optimizer (150 combos, 2 blocks) | Executor | ✅ |
| `phase2b_horaire_optimization.py` | Horaire optimizer (6 UTC profiles) | Executor | ✅ |
| `phase2c_volatility_optimization.py` | Volatility optimizer (5 ATR bands) | Executor | ✅ |

### Consolidation Scripts

| File | Purpose | Type | Status |
|------|---------|------|--------|
| `phase2a_consolidate_blocks.py` | Merge Phase 2a blocks 1+2 into single best | Utility | ✅ |
| `phase2_combine_results.py` | Merge Phase 2a+2b+2c into final Phase 2 result | Utility | ✅ |

### Master Scripts

| File | Purpose | Type | Status |
|------|---------|------|--------|
| `run_phase2_full.py` | Execute all phases in sequence (automated) | Master | ✅ |

### Documentation

| File | Purpose | Type | Status |
|------|---------|------|--------|
| `PHASE2_OPTIMIZATION_README.md` | Complete Phase 2 workflow documentation | Docs | ✅ |
| `PHASE2_SCRIPTS_STATUS.md` | This file - creation status | Status | ✅ |

---

## Execution Options

### Quick Start (All-in-One)
```bash
python run_phase2_full.py
```
- Automatically runs all phases in correct sequence
- Shows progress for each phase
- Estimated time: 20-25 min

### VPS Parallel Execution (Fastest)
```bash
# Terminal 1
python phase2a_trend_optimization_block_runner_vec.py 1

# Terminal 2 (can start immediately)
python phase2a_trend_optimization_block_runner_vec.py 2

# After both blocks complete:
python phase2a_consolidate_blocks.py
python phase2b_horaire_optimization.py
python phase2c_volatility_optimization.py
python phase2_combine_results.py
```
- Estimated time: 13-15 min (blocks 1+2 in parallel)

### Step-by-Step Execution
```bash
# Phase 2a - Block 1
python phase2a_trend_optimization_block_runner_vec.py 1

# Phase 2a - Block 2
python phase2a_trend_optimization_block_runner_vec.py 2

# Phase 2a - Consolidate
python phase2a_consolidate_blocks.py

# Phase 2b - Horaire
python phase2b_horaire_optimization.py

# Phase 2c - Volatility
python phase2c_volatility_optimization.py

# Phase 2 - Final Consolidation
python phase2_combine_results.py
```

---

## Expected Output Files

### Phase 2a Outputs (Trend Filter)
```
phase2a_trend_optimization_block_1_log.csv
phase2a_trend_optimization_block_1_best_params.json
phase2a_trend_optimization_block_1_top10.csv

phase2a_trend_optimization_block_2_log.csv
phase2a_trend_optimization_block_2_best_params.json
phase2a_trend_optimization_block_2_top10.csv

phase2a_trend_full_log.csv                    [consolidated]
phase2a_trend_best_params.json                [BEST - loads into 2b/2c]
```

### Phase 2b Outputs (Horaire)
```
phase2b_horaire_optimization_log.csv          [6 rows - all profiles]
phase2b_horaire_best_params.json              [BEST - loads into 2c]
```

### Phase 2c Outputs (Volatility)
```
phase2c_volatility_optimization_log.csv       [5 rows - all bands]
phase2c_volatility_best_params.json           [BEST - locked for Phase 3]
```

### Phase 2 Consolidation Outputs
```
phase2_best_params.json                       [Phase 1+2 combined, final]
phase3_summary.json                           [Locked params ready for Phase 3]
```

---

## Dependencies

### Required Files (from Phase 1)
- ✅ `YM_phase_A_clean.csv` (training data)
- ✅ `YM_phase_B_clean.csv` (validation data)
- ✅ `phase1_best_params.json` (Phase 1 signal best)
- ✅ `COMB_001_TREND_V1_vectorized.py` (backtest engine)

### Python Environment
- Python 3.8+
- numpy (for vectorization)
- Standard library: csv, json, pathlib, subprocess, time, multiprocessing

---

## Locking Strategy

### Phase 1 (LOCKED for Phase 2)
```
stpmt_smooth_h: 3
stpmt_smooth_b: 2
stpmt_distance_max_h: 50
stpmt_distance_max_l: 50
Robustness: 1.3424
```

### Phase 2a → 2b → 2c Cascade
```
Phase 2a Output        Phase 2b Input         Phase 2c Input
─────────────────────────────────────────────────────────
trend_r1, r2, r3   ──→ (locked)          ──→ (locked)
                       horaire_hours    ──→ (locked)
                                            volatility_atr_min/max
```

### Phase 2 → Phase 3
```
Phase 2 Output
─────────────────────────────────────────
stpmt_smooth_h (locked)
stpmt_smooth_b (locked)
stpmt_distance_max_h (locked)
stpmt_distance_max_l (locked)
trend_r1, r2, r3 (locked)
horaire_allowed_hours_utc (locked)
volatility_atr_min, atr_max (locked)

Phase 3 will optimize:
target_atr_multiplier: [5.0, 10.0, 15.0, 20.0]
timescan_bars: [20, 30, 40, 50]
```

---

## Execution Checklist

Before running Phase 2:

- [ ] Phase 1 completed (block 1-5)
- [ ] `phase1_best_params.json` exists
- [ ] `YM_phase_A_clean.csv` exists
- [ ] `YM_phase_B_clean.csv` exists
- [ ] `COMB_001_TREND_V1_vectorized.py` is in same directory

---

## Quick Reference

### Phase 2a: Trend Filter
- **Combos:** 150 (5 × 6 × 5)
- **Blocks:** 2 (Block 1: 60, Block 2: 90)
- **Time:** 13-15 min (parallel) or 20-25 min (sequential)
- **Parallelism:** Yes, Pool-based
- **Grid:**
  - r1: [1, 2, 3, 4, 5]
  - r2: [50, 70, 90, 110, 130, 150]
  - r3: [100, 150, 200, 250, 300]

### Phase 2b: Horaire
- **Profiles:** 6 sequential
- **Time:** ~3 min
- **Parallelism:** No (sequential tests)
- **Options:**
  - [0-23], [9-15], [9-17], [8-16], [9-12], [12-15]

### Phase 2c: Volatility
- **Profiles:** 5 sequential
- **Time:** ~3 min
- **Parallelism:** No (sequential tests)
- **Options:**
  - (0, 500), (10, 500), (0, 200), (10, 250), (20, 200)

---

## Success Criteria

Each sub-phase must achieve:
- ✅ Phase B Profit Factor ≥ 1.3
- ✅ Robustness (PF_B / PF_A) ≥ 0.80
- ✅ Minimum trade count ≥ 50-100 (depending on filters)

---

## Next Steps After Phase 2

1. Review `phase2_best_params.json` - confirm all robustness values
2. Verify `phase3_summary.json` has correct locked parameters
3. Create Phase 3 optimization scripts:
   - `phase3_exits_optimization_block_runner_vec.py` (16 combos)
   - `phase3_consolidate_results.py`
   - `run_phase3_full.py`
4. Launch Phase 3 (Exits optimization: target_atr_multiplier + timescan_bars)

---

## Support

For detailed documentation, see: `PHASE2_OPTIMIZATION_README.md`

For debugging issues, check:
- CSV logs for metrics across all combos/profiles
- JSON files for best params structure
- Console output for timing and error messages

---
