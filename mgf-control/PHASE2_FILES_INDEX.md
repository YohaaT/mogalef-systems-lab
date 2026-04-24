# Phase 2 Optimization - Complete File Index

**Created:** 2026-04-22  
**Status:** ✅ READY FOR EXECUTION

---

## Directory Structure

```
mgf-control/
├── COMB_001_TREND_V1.py                           [EXISTING - main strategy]
├── COMB_001_TREND_V1_vectorized.py                [EXISTING - vectorized version]
│
├── phase1_best_params.json                        [EXISTING - from Phase 1]
│
├─ PHASE 2 EXECUTORS ──────────────────────────────
├── phase2a_trend_optimization_block_runner_vec.py [NEW - runs 2 blocks of 150 combos]
├── phase2b_horaire_optimization.py                [NEW - runs 6 horaire profiles]
├── phase2c_volatility_optimization.py             [NEW - runs 5 volatility bands]
│
├─ PHASE 2 UTILITIES ──────────────────────────────
├── phase2a_consolidate_blocks.py                  [NEW - merges 2a blocks]
├── phase2_combine_results.py                      [NEW - merges 2a/2b/2c results]
├── run_phase2_full.py                             [NEW - master executor (automated)]
│
├─ PHASE 2 DOCUMENTATION ──────────────────────────
├── PHASE2_OPTIMIZATION_README.md                  [NEW - comprehensive guide]
├── PHASE2_SCRIPTS_STATUS.md                       [NEW - creation status]
├── PHASE2_FILES_INDEX.md                          [NEW - this file]
│
├─ OUTPUT DIRECTORIES (created during execution) ──
├── phase2a_trend_optimization_block_1_log.csv     [60 rows]
├── phase2a_trend_optimization_block_1_best_params.json
├── phase2a_trend_optimization_block_1_top10.csv
├── phase2a_trend_optimization_block_2_log.csv     [90 rows]
├── phase2a_trend_optimization_block_2_best_params.json
├── phase2a_trend_optimization_block_2_top10.csv
├── phase2a_trend_full_log.csv                     [150 rows consolidated]
├── phase2a_trend_best_params.json                 [LOADS INTO 2b/2c]
│
├── phase2b_horaire_optimization_log.csv           [6 rows]
├── phase2b_horaire_best_params.json               [LOADS INTO 2c]
│
├── phase2c_volatility_optimization_log.csv        [5 rows]
├── phase2c_volatility_best_params.json            [LOCKED FOR PHASE 3]
│
├── phase2_best_params.json                        [FINAL - Phase 1+2 combined]
└── phase3_summary.json                            [READY FOR PHASE 3]
```

---

## File Descriptions

### Core Executors (Run These)

#### `phase2a_trend_optimization_block_runner_vec.py` (270 lines)
**Purpose:** Optimize Trend Filter parameters (trend_r1, trend_r2, trend_r3)

**Execution:**
```bash
python phase2a_trend_optimization_block_runner_vec.py 1    # Block 1: r1=[1,2] (60 combos)
python phase2a_trend_optimization_block_runner_vec.py 2    # Block 2: r1=[3,4,5] (90 combos)
```

**Grid:**
- trend_r1: [1, 2, 3, 4, 5]
- trend_r2: [50, 70, 90, 110, 130, 150]
- trend_r3: [100, 150, 200, 250, 300]

**Locks:** Phase 1 signal best (smooth_h=3, smooth_b=2, dist=50/50)

**Outputs:**
- `phase2a_trend_optimization_block_N_log.csv`
- `phase2a_trend_optimization_block_N_best_params.json`
- `phase2a_trend_optimization_block_N_top10.csv`

**Time:** ~5 min (Block 1) + ~8 min (Block 2) = ~13 min total (or parallel on VPS)

---

#### `phase2b_horaire_optimization.py` (260 lines)
**Purpose:** Optimize UTC allowed trading hours

**Execution:**
```bash
python phase2b_horaire_optimization.py
```

**Profiles:**
1. [0-23] - Trade all hours
2. [9-15] - US regular
3. [9-17] - US extended
4. [8-16] - Pre-market
5. [9-12] - Morning only
6. [12-15] - Afternoon only

**Locks:**
- Phase 1 signal best
- Phase 2a trend best (loads from `phase2a_trend_best_params.json`)

**Outputs:**
- `phase2b_horaire_optimization_log.csv`
- `phase2b_horaire_best_params.json`

**Time:** ~3 min

---

#### `phase2c_volatility_optimization.py` (250 lines)
**Purpose:** Optimize ATR volatility bounds

**Execution:**
```bash
python phase2c_volatility_optimization.py
```

**Profiles:**
1. (0, 500) - No filter
2. (10, 500) - Min floor
3. (0, 200) - Max ceiling
4. (10, 250) - Tight band
5. (20, 200) - Very selective

**Locks:**
- Phase 1 signal best
- Phase 2a trend best
- Phase 2b horaire best (loads from `phase2b_horaire_best_params.json`)

**Outputs:**
- `phase2c_volatility_optimization_log.csv`
- `phase2c_volatility_best_params.json`

**Time:** ~3 min

---

### Utility Scripts (Run After Sub-Phases)

#### `phase2a_consolidate_blocks.py` (160 lines)
**Purpose:** Merge Phase 2a Block 1 + Block 2 results into single best

**Execution:**
```bash
python phase2a_consolidate_blocks.py
```

**Inputs:**
- `phase2a_trend_optimization_block_1_log.csv`
- `phase2a_trend_optimization_block_1_best_params.json`
- `phase2a_trend_optimization_block_2_log.csv`
- `phase2a_trend_optimization_block_2_best_params.json`

**Outputs:**
- `phase2a_trend_full_log.csv` (150 rows, sorted by robustness)
- `phase2a_trend_best_params.json` (best across both blocks)

**Time:** ~1 min

---

#### `phase2_combine_results.py` (210 lines)
**Purpose:** Consolidate Phase 2a/2b/2c results into final Phase 2 params

**Execution:**
```bash
python phase2_combine_results.py
```

**Inputs:**
- `phase1_best_params.json`
- `phase2a_trend_best_params.json`
- `phase2b_horaire_best_params.json`
- `phase2c_volatility_best_params.json`

**Outputs:**
- `phase2_best_params.json` (Phase 1+2 locked params for Phase 3)
- `phase3_summary.json` (ready for Phase 3 executor script creation)

**Time:** ~30 sec

---

### Master Executor (Recommended)

#### `run_phase2_full.py` (150 lines)
**Purpose:** Execute all Phase 2 sub-phases in correct sequence (automated)

**Execution:**
```bash
python run_phase2_full.py
```

**Workflow:**
1. Checks data files
2. Runs Phase 2a Block 1
3. Runs Phase 2a Block 2
4. Consolidates Phase 2a
5. Runs Phase 2b (depends on Phase 2a)
6. Runs Phase 2c (depends on Phase 2b)
7. Consolidates all Phase 2 results

**Outputs:** All Phase 2a/2b/2c + consolidated files

**Time:** ~20-25 min (or 13-15 min if blocks 1+2 run in parallel on VPS)

---

### Documentation

#### `PHASE2_OPTIMIZATION_README.md` (340 lines)
Comprehensive guide covering:
- Overview of Phase 2 architecture
- Phase 2a (Trend Filter) details
- Phase 2b (Horaire) details
- Phase 2c (Volatility) details
- Execution options (automated, VPS parallel, step-by-step)
- File formats (CSV/JSON)
- Requirements and dependencies
- Diagnostics and troubleshooting
- Next steps (Phase 3)

---

#### `PHASE2_SCRIPTS_STATUS.md` (280 lines)
Quick reference covering:
- Summary of what was created
- Created files table
- Execution options
- Expected output files
- Dependencies
- Locking strategy
- Execution checklist
- Quick reference (combos, blocks, time, grids)
- Success criteria
- Next steps

---

#### `PHASE2_FILES_INDEX.md` (This file)
Complete file listing with descriptions, execution commands, inputs/outputs, and time estimates.

---

## Execution Workflows

### Workflow 1: All-in-One (Simplest)
```bash
python run_phase2_full.py
```
✅ Runs all phases automatically  
⏱️ Time: 20-25 min

---

### Workflow 2: VPS Parallel + Local (Fastest)
```bash
# Terminal 1 on VPS
python phase2a_trend_optimization_block_runner_vec.py 1

# Terminal 2 on VPS (starts immediately)
python phase2a_trend_optimization_block_runner_vec.py 2

# After blocks finish, run on local/VPS:
python phase2a_consolidate_blocks.py
python phase2b_horaire_optimization.py
python phase2c_volatility_optimization.py
python phase2_combine_results.py
```
✅ Blocks 1+2 run in parallel  
⏱️ Time: 13-15 min

---

### Workflow 3: Manual Step-by-Step
```bash
# Step 1: Phase 2a Block 1
python phase2a_trend_optimization_block_runner_vec.py 1

# Step 2: Phase 2a Block 2
python phase2a_trend_optimization_block_runner_vec.py 2

# Step 3: Consolidate Phase 2a
python phase2a_consolidate_blocks.py

# Step 4: Phase 2b (auto-loads Phase 2a best)
python phase2b_horaire_optimization.py

# Step 5: Phase 2c (auto-loads Phase 2a+2b best)
python phase2c_volatility_optimization.py

# Step 6: Consolidate all Phase 2
python phase2_combine_results.py
```
✅ Full control over each step  
⏱️ Time: 20-25 min

---

## Input/Output Chain

```
PHASE 1 OUTPUT
└─ phase1_best_params.json
   └─ PHASE 2a (Block 1+2)
      └─ phase2a_trend_best_params.json
         └─ PHASE 2b
            └─ phase2b_horaire_best_params.json
               └─ PHASE 2c
                  └─ phase2c_volatility_best_params.json
                     └─ CONSOLIDATION
                        └─ phase2_best_params.json
                           └─ PHASE 3
```

---

## File Sizes (Estimated)

| File | Size | Rows |
|------|------|------|
| phase2a_trend_full_log.csv | 45 KB | 150 |
| phase2b_horaire_optimization_log.csv | 2 KB | 6 |
| phase2c_volatility_optimization_log.csv | 2 KB | 5 |
| phase2_best_params.json | 2 KB | - |
| phase3_summary.json | 1 KB | - |

---

## Validation

After Phase 2 completes, verify:

```bash
# Check Phase 2a consolidated
wc -l phase2a_trend_full_log.csv                # Should be 151 (header + 150 rows)

# Check Phase 2b
wc -l phase2b_horaire_optimization_log.csv      # Should be 7 (header + 6 rows)

# Check Phase 2c
wc -l phase2c_volatility_optimization_log.csv   # Should be 6 (header + 5 rows)

# Check final params exist
ls -l phase2_best_params.json
ls -l phase3_summary.json

# View final best params
cat phase2_best_params.json
```

---

## Success Metrics

✅ All sub-phases completed  
✅ All robustness values ≥ 0.80  
✅ phase2_best_params.json generated  
✅ phase3_summary.json ready for Phase 3  
✅ No errors in console output  

---

## Troubleshooting

**Q: Block 2 won't start (missing phase2a_trend_best_params.json)**  
A: Ensure Block 1 completed. Run: `python phase2a_consolidate_blocks.py`

**Q: Phase 2b fails (missing phase2a_trend_best_params.json)**  
A: Ensure Phase 2a consolidation completed. Check file exists.

**Q: Phase 2c fails (missing phase2b_horaire_best_params.json)**  
A: Ensure Phase 2b completed. Run: `python phase2b_horaire_optimization.py`

**Q: Low robustness values (< 0.80)**  
A: Check CSV logs for trade counts. May need to adjust filter bounds.

---

## Next: Phase 3 Planning

After Phase 2 completes, create:
1. `phase3_exits_optimization_block_runner_vec.py` (16 combos: 4 ATR mult × 4 TimeStop bars)
2. `phase3_consolidate_results.py`
3. `run_phase3_full.py`

Locked params from Phase 2 will be used.

---

## Quick Commands

```bash
# Run everything
python run_phase2_full.py

# Run just Phase 2a blocks
python phase2a_trend_optimization_block_runner_vec.py 1 && \
python phase2a_trend_optimization_block_runner_vec.py 2

# Consolidate Phase 2a
python phase2a_consolidate_blocks.py

# Run Phase 2b + 2c sequentially
python phase2b_horaire_optimization.py && python phase2c_volatility_optimization.py

# Consolidate all Phase 2
python phase2_combine_results.py

# View results
cat phase2_best_params.json
```

---
