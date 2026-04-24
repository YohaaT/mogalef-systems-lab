# Phase 2 Optimization: Contexto Filters

## Overview

Phase 2 optimizes the **Contexto component** (Trend Filter + Horaire + Volatility) while keeping the **Signal component** (from Phase 1) locked.

**Phase 1 Best (LOCKED):**
- `stpmt_smooth_h: 3`
- `stpmt_smooth_b: 2`
- `stpmt_distance_max_h: 50`
- `stpmt_distance_max_l: 50`
- Robustness: **1.3424**

---

## Architecture

### Phase 2a: Trend Filter Optimization

**Grid Size:** 150 combinations
- `trend_r1`: [1, 2, 3, 4, 5] (5 values)
- `trend_r2`: [50, 70, 90, 110, 130, 150] (6 values)
- `trend_r3`: [100, 150, 200, 250, 300] (5 values)
- **Total:** 5 × 6 × 5 = 150 combos

**Execution:** 2 blocks with parallelism (Pool)
- **Block 1:** r1=[1,2], 2×6×5 = 60 combos (~5 min on 8 cores)
- **Block 2:** r1=[3,4,5], 3×6×5 = 90 combos (~8 min on 8 cores)

**Output Files:**
```
phase2a_trend_optimization_block_1_log.csv      (60 rows)
phase2a_trend_optimization_block_1_best_params.json
phase2a_trend_optimization_block_1_top10.csv

phase2a_trend_optimization_block_2_log.csv      (90 rows)
phase2a_trend_optimization_block_2_best_params.json
phase2a_trend_optimization_block_2_top10.csv

phase2a_trend_full_log.csv                      (150 rows consolidated)
phase2a_trend_best_params.json                  (best across both blocks)
```

**Success Criteria:**
- Phase B PF ≥ 1.3
- Robustness ≥ 0.80
- Trade count ≥ 100 on Phase A

---

### Phase 2b: Horaire (UTC Hours) Optimization

**Profiles:** 6 sequential tests (no parallelism)

| # | Name | Hours | Description |
|---|------|-------|-------------|
| 1 | no_filter | [0-23] | Trade all hours |
| 2 | us_regular | [9-15] | US regular session |
| 3 | us_extended | [9-17] | US extended |
| 4 | pre_market | [8-16] | Pre-market + regular |
| 5 | morning | [9-12] | Morning only |
| 6 | afternoon | [12-15] | Afternoon only |

**Execution:** Sequential, ~30s per test (~3 min total)

**Locks:**
- Phase 1 signal best (smooth_h=3, smooth_b=2, dist=50/50)
- Phase 2a trend best (loaded from phase2a_trend_best_params.json)

**Output Files:**
```
phase2b_horaire_optimization_log.csv            (6 rows)
phase2b_horaire_best_params.json                (best profile)
```

**Success Criteria:**
- Phase B PF ≥ 1.3
- Robustness ≥ 0.80
- Improvement over default horaire [9-15]

---

### Phase 2c: Volatility (ATR Bounds) Optimization

**Profiles:** 5 sequential tests (no parallelism)

| # | Name | ATR Min | ATR Max | Description |
|---|------|---------|---------|-------------|
| 1 | no_filter | 0 | 500 | No volatility filter |
| 2 | min_floor | 10 | 500 | Minimum floor |
| 3 | max_ceiling | 0 | 200 | Maximum ceiling |
| 4 | tight_band | 10 | 250 | Tight band |
| 5 | very_selective | 20 | 200 | Very selective |

**Execution:** Sequential, ~30s per test (~3 min total)

**Locks:**
- Phase 1 signal best (smooth_h=3, smooth_b=2, dist=50/50)
- Phase 2a trend best
- Phase 2b horaire best

**Output Files:**
```
phase2c_volatility_optimization_log.csv         (5 rows)
phase2c_volatility_best_params.json             (best band)
```

**Success Criteria:**
- Phase B PF ≥ 1.3
- Robustness ≥ 0.80
- Trade count ≥ 50 on Phase A

---

## Execution

### Option 1: Run Full Phase 2 (Automated)

```bash
python run_phase2_full.py
```

**Estimated Time:**
- Phase 2a Block 1: ~5 min
- Phase 2a Block 2: ~8 min
- Phase 2a Consolidate: ~1 min
- Phase 2b: ~3 min
- Phase 2c: ~3 min
- **Total: ~20-25 min**

### Option 2: Run Individual Phases

**Phase 2a - Block 1 only:**
```bash
python phase2a_trend_optimization_block_runner_vec.py 1
```

**Phase 2a - Block 2 only:**
```bash
python phase2a_trend_optimization_block_runner_vec.py 2
```

**Phase 2a - Consolidate both blocks:**
```bash
python phase2a_consolidate_blocks.py
```

**Phase 2b - Horaire (depends on Phase 2a best):**
```bash
python phase2b_horaire_optimization.py
```

**Phase 2c - Volatility (depends on Phase 2a + 2b best):**
```bash
python phase2c_volatility_optimization.py
```

**Phase 2 - Consolidate all sub-phases:**
```bash
python phase2_combine_results.py
```

### Option 3: Run on VPS (Parallel Blocks)

**Terminal 1 - Block 1:**
```bash
python phase2a_trend_optimization_block_runner_vec.py 1
```

**Terminal 2 - Block 2 (can start immediately):**
```bash
python phase2a_trend_optimization_block_runner_vec.py 2
```

Both blocks can run in parallel. Once both complete, run consolidation and continue with 2b/2c.

---

## Files Generated

### After Phase 2a (Trend Filter)
```
phase2a_trend_optimization_block_1_log.csv
phase2a_trend_optimization_block_1_best_params.json
phase2a_trend_optimization_block_1_top10.csv

phase2a_trend_optimization_block_2_log.csv
phase2a_trend_optimization_block_2_best_params.json
phase2a_trend_optimization_block_2_top10.csv

phase2a_trend_full_log.csv                      [consolidated]
phase2a_trend_best_params.json                  [best result]
```

### After Phase 2b (Horaire)
```
phase2b_horaire_optimization_log.csv
phase2b_horaire_best_params.json
```

### After Phase 2c (Volatility)
```
phase2c_volatility_optimization_log.csv
phase2c_volatility_best_params.json
```

### After Phase 2 Consolidation
```
phase2_best_params.json                         [Phase 1+2 combined]
phase3_summary.json                             [locked params for Phase 3]
```

---

## CSV Format

**phase2a_trend_optimization_block_N_log.csv:**
```
block,combo,trend_r1,trend_r2,trend_r3,
phase_a_pf,phase_a_wr,phase_a_trades,phase_a_equity,
phase_b_pf,phase_b_wr,phase_b_trades,phase_b_equity,
robustness
```

**phase2b_horaire_optimization_log.csv:**
```
profile_id,profile_name,hours,
phase_a_pf,phase_a_wr,phase_a_trades,phase_a_equity,
phase_b_pf,phase_b_wr,phase_b_trades,phase_b_equity,
robustness
```

**phase2c_volatility_optimization_log.csv:**
```
profile_id,profile_name,atr_min,atr_max,
phase_a_pf,phase_a_wr,phase_a_trades,phase_a_equity,
phase_b_pf,phase_b_wr,phase_b_trades,phase_b_equity,
robustness
```

---

## JSON Format

**phase2a_trend_best_params.json:**
```json
{
  "block": 1,
  "trend_r1": 2,
  "trend_r2": 90,
  "trend_r3": 150,
  "robustness": 0.8234,
  "phase_a_pf": 1.523,
  "phase_b_pf": 1.255
}
```

**phase2b_horaire_best_params.json:**
```json
{
  "profile_id": 2,
  "profile_name": "us_regular",
  "hours": [9, 10, 11, 12, 13, 14, 15],
  "robustness": 0.8120,
  "phase_a_pf": 1.523,
  "phase_b_pf": 1.237
}
```

**phase2_best_params.json (final):**
```json
{
  "phase": 2,
  "signal_from_phase1": {
    "stpmt_smooth_h": 3,
    "stpmt_smooth_b": 2,
    "stpmt_distance_max_h": 50,
    "stpmt_distance_max_l": 50,
    "phase1_robustness": 1.3424
  },
  "trend_filter_best": {
    "trend_r1": 2,
    "trend_r2": 90,
    "trend_r3": 150,
    "phase2a_robustness": 0.8234
  },
  "horaire_best": {
    "horaire_allowed_hours_utc": [9, 10, 11, 12, 13, 14, 15],
    "phase2b_robustness": 0.8120
  },
  "volatility_best": {
    "volatility_atr_min": 10.0,
    "volatility_atr_max": 250.0,
    "phase2c_robustness": 0.8050
  },
  "overall_phase2_robustness": 0.8050
}
```

---

## Requirements

**Data Files:**
- `YM_phase_A_clean.csv` (training set, required)
- `YM_phase_B_clean.csv` (validation set, required)
- `phase1_best_params.json` (from Phase 1, required)

**Python Modules:**
- `COMB_001_TREND_V1_vectorized.py` (vectorized backtest engine)
- Standard: `csv`, `json`, `pathlib`, `subprocess`, `time`

---

## Diagnostics

### Check Phase 2a Progress
```bash
ls -lh phase2a_trend_optimization_block_*
wc -l phase2a_trend_optimization_block_1_log.csv  # Should show 61 (header + 60 combos)
```

### View Phase 2a Top 10
```bash
head -11 phase2a_trend_optimization_block_1_top10.csv
```

### Check Phase 2b Results
```bash
cat phase2b_horaire_optimization_log.csv | cut -d, -f2,12
```

### View Final Best Params
```bash
cat phase2_best_params.json
```

---

## Next Steps

After Phase 2 completes successfully:

1. **Review** `phase2_best_params.json` - confirm all sub-phase robustness ≥ 0.80
2. **Verify** Phase B robustness: `phase_b_pf ÷ phase_a_pf ≥ 0.80`
3. **Launch Phase 3** with locked Phase 1+2 params
4. **Phase 3** optimizes Exits:
   - `target_atr_multiplier`: [5.0, 10.0, 15.0, 20.0]
   - `timescan_bars`: [20, 30, 40, 50]
   - Grid: 4 × 4 = 16 combos (~2 min)

---

## Troubleshooting

**Error: "No Phase 2a best params found. Run phase2a first!"**
- Ensure Phase 2a blocks completed successfully
- Check: `phase2a_trend_optimization_block_1_best_params.json` and `_block_2_best_params.json` exist
- Run: `python phase2a_consolidate_blocks.py`

**Error: "No Phase 2b best params found. Run phase2b first!"**
- Phase 2a must complete before running Phase 2b
- Check: `phase2a_trend_best_params.json` exists
- Run: `python phase2b_horaire_optimization.py`

**Error: "No Phase 2c best params found. Run phase2c first!"**
- Phase 2b must complete before running Phase 2c
- Check: `phase2b_horaire_best_params.json` exists
- Run: `python phase2c_volatility_optimization.py`

**Low robustness (< 0.80):**
- Check Phase A trade count - if < 100, might be over-filtering
- Review CSV logs to identify which sub-phase is causing degradation
- Consider expanding bounds (e.g., wider horaire, wider volatility band)

---

## Performance Notes

**Vectorization Impact:**
- Phase 2a: 13-15 min for 150 combos (vectorized + Pool)
- Phase 1 equivalent: 40-50 min (no vectorization)
- **Speedup: 3-4x**

**VPS Execution:**
- Block 1 and Block 2 can run in parallel (bilateral)
- Blocks 1+2 in parallel: ~8 min
- Sequential: ~13 min

**Local Execution:**
- Phase 2b/2c are fast enough to run locally (~3 min each)
- Can run while Phase 2a blocks execute on VPS

---

## Validation Checklist

- [ ] Phase 2a Block 1 complete (60 combos)
- [ ] Phase 2a Block 2 complete (90 combos)
- [ ] Phase 2a consolidated (150 combos)
- [ ] Phase 2a best robustness ≥ 0.80
- [ ] Phase 2b complete (6 profiles)
- [ ] Phase 2b best robustness ≥ 0.80
- [ ] Phase 2c complete (5 bands)
- [ ] Phase 2c best robustness ≥ 0.80
- [ ] phase2_best_params.json generated
- [ ] phase3_summary.json generated
- [ ] Overall Phase 2 robustness ≥ 0.80

---
