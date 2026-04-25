# TANK VEC+POOL Implementation Plan — Phases 1-5

**Status:** TANK STOPPED — Awaiting implementation
**Date:** 2026-04-25
**Goal:** Implement proper VEC+POOL optimization for TANK Phases 1-5, well-tested before deployment

---

## Context

### Current State
- **BO:** Running Phases 1-5 with POOL only (no VEC). Has completed Phases 1-4 for 5 pipelines (ES 15m, FDAX 15m, MNQ 15m). Continue letting BO run as-is.
- **TANK:** STOPPED after 2 attempts (with bug fixes). Ready for proper VEC+POOL implementation.
- **Prior failed attempt:** `COMB_001_TREND_V1_vectorized.py` was 35% slower than non-VEC because it still has bar-by-bar backtest loop with numpy overhead.

### Problem Diagnosis (Why Previous VEC Failed)
1. `COMB_001_TREND_V1_vectorized.py` only vectorized ATR calculation (small fraction of compute)
2. Main backtest loop (bar-by-bar) NOT vectorized (impossible — sequential by nature)
3. NumPy overhead exceeded vectorization gains for small arrays
4. Net result: 35% slowdown (0.74x speedup)

### Pending Issue (Documented for Later)
- **MNQ 15m COMB_001 returns 0 trades in Phase 1 POOL** (both BO and TANK)
- Direct test (no POOL) generates 3500+ trades correctly
- Suggests Pool worker exception handling silencing real error
- TODO: Add detailed exception logging in worker function

---

## Implementation Strategy: "VEC+POOL Bien Hecho"

### Principle
**Vectorize what's vectorizable, accept what's not.** Don't try to vectorize bar-by-bar backtest logic. Focus on indicator pre-calculation that runs ONCE per combo.

### What CAN Be Vectorized (High Gain)
| Component | Current | Vectorized | Speedup |
|-----------|---------|-----------|---------|
| ATR calculation | for-loop O(n) | numpy O(n) vectorized | 5-10x |
| STPMT_DIV smoothing | for-loop | numpy convolve | 8-15x |
| STPMT_DIV distance | for-loop | numpy where/clip | 5-8x |
| Trend Filter MTF | for-loop | numpy rolling | 6-10x |
| Stop Intelligent ATR | already partial | numpy full | 3-5x |
| Volatility filter | for-loop | numpy boolean | 10-20x |

### What CANNOT Be Vectorized (Keep Sequential)
- Bar-by-bar backtest loop (entry/exit decisions depend on previous bar state)
- Trade lifecycle management (active position tracking)
- Stop adjustment logic (depends on current trade state)

### Expected Net Gain
- **Indicator pre-calculation:** 30-50% time saved per combo
- **POOL parallelization:** 6x speedup (workers=6 on 8 cores)
- **Total Phase 1 speedup:** ~5-8x vs sequential non-VEC

---

## Implementation Phases

### PHASE A: Analysis (1-2 hours)

#### Tasks
- [ ] Profile `COMB_001_TREND_V1.py` to identify hot paths
  - Measure: `time strat.run(data)` for 1 combo on MNQ 15m
  - Profile: cProfile to find which functions consume most time
  - Expected: Indicator calc (40-50%), backtest loop (50-60%)
- [ ] Profile `COMB_002_IMPULSE_V2_adaptive.py` similarly
- [ ] Identify components NOT yet vectorized in `COMB_001_TREND_V1_vectorized.py`
  - Currently only ATR is vectorized
  - STPMT_DIV, Trend Filter, etc. still loop-based
- [ ] Document baseline times:
  - Single combo time: ~9.3s on MNQ 15m (189k rows)
  - 400 combos sequential: ~62 minutes
  - 400 combos POOL(6): ~10-12 minutes (current TANK)

#### Deliverable
- `docs/profiling_results.md` with hot-path analysis

---

### PHASE B: Build Optimized Vectorized Strategy (3-4 hours)

#### B.1: Create `COMB_001_TREND_V1_vec_optimized.py`

**Vectorize these functions:**

```python
def vectorized_atr(high, low, close, period=14):
    """Full numpy vectorization of ATR — currently partial."""
    high = np.asarray(high)
    low = np.asarray(low)
    close = np.asarray(close)
    
    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    tr[0] = tr1[0]  # First bar has no previous close
    
    # Wilder's smoothing as vectorized
    atr = np.zeros_like(tr)
    atr[period-1] = tr[:period].mean()
    for i in range(period, len(tr)):
        atr[i] = (atr[i-1] * (period-1) + tr[i]) / period
    return atr


def vectorized_stpmt_div(close, smooth_h, smooth_b, dist_max_h, dist_max_l):
    """Vectorized STPMT_DIV indicator."""
    # Use numpy convolve for smoothing
    kernel_h = np.ones(smooth_h) / smooth_h
    kernel_b = np.ones(smooth_b) / smooth_b
    
    smooth_h_arr = np.convolve(close, kernel_h, mode='valid')
    smooth_b_arr = np.convolve(close, kernel_b, mode='valid')
    
    # Distance calculations vectorized
    dist_h = np.abs(close[smooth_h-1:] - smooth_h_arr)
    dist_l = np.abs(close[smooth_b-1:] - smooth_b_arr)
    
    # Boolean filtering
    valid_h = dist_h <= dist_max_h
    valid_l = dist_l <= dist_max_l
    
    return {'pose': ..., 'valid': valid_h & valid_l}
```

**Key changes:**
- Replace all `for i in range(n)` with numpy operations
- Use boolean masking instead of conditional appends
- Pre-allocate arrays (no list growing)
- Use `np.cumsum`, `np.where`, `np.clip` instead of loops

#### B.2: Create `COMB_002_IMPULSE_V2_vec_optimized.py`

Same pattern as B.1 for COMB_002:
- Vectorize Intelligent Scalping Target calculation
- Vectorize Super Stop Long/Short ATR calculations
- Keep backtest loop sequential (unavoidable)

#### B.3: Equivalence Test

```python
# test_vec_optimized_equivalence.py
def test_results_match():
    """VEC optimized must produce IDENTICAL results to non-VEC."""
    for combo in test_combos:
        result_nonvec = Comb001TrendStrategy(params).run(data)
        result_vec = Comb001TrendVecOptimized(params).run(data)
        
        assert len(result_nonvec.trades) == len(result_vec.trades)
        assert abs(result_nonvec.profit_factor - result_vec.profit_factor) < 0.001
        assert abs(result_nonvec.max_drawdown - result_vec.max_drawdown) < 0.01
```

#### Deliverable
- `mgf-control/COMB_001_TREND_V1_vec_optimized.py`
- `mgf-control/COMB_002_IMPULSE_V2_vec_optimized.py`
- `mgf-control/test_vec_optimized_equivalence.py`

---

### PHASE C: Build VEC+POOL Phase Scripts (2 hours)

#### C.1: Phase 1 Script

`phase1_signal_independent_pool_vec_opt.py`:
- Same as `phase1_signal_independent_pool.py`
- Change imports:
  ```python
  from COMB_001_TREND_V1_vec_optimized import Comb001TrendVecOptimized as Comb001TrendStrategy
  from COMB_002_IMPULSE_V2_vec_optimized import Comb002ImpulseV2VecOptimized as Comb002ImpulseV2Strategy
  ```
- Same POOL(6) configuration
- Same grid (400 combos)

#### C.2: Phase 2a, 2b, 3, 4 Scripts

Same pattern — only import changes:
- `phase2a_horaire_independent_pool_vec_opt.py`
- `phase2b_regime_independent_pool_vec_opt.py`
- `phase3_exits_independent_pool_vec_opt.py`
- `phase4_stops_independent_pool_vec_opt.py`

#### C.3: Phase 5 Script

`phase5_combine_filters_vec_opt.py`:
- Already exists as `phase5_combine_filters_vectorized.py`
- May need to update imports to use new VEC strategies

#### Deliverable
- 5 new `phase*_pool_vec_opt.py` scripts
- All using new VEC-optimized strategy classes

---

### PHASE D: Local Testing (2-3 hours)

#### D.1: Single-Combo Benchmark

```bash
# Test 1: Time a single combo
python3 test_vec_opt_single_combo.py
# Expected: VEC < 6s/combo (vs 9.3s non-VEC)
```

#### D.2: POOL(6) Benchmark

```bash
# Test 2: Time 100 combos with POOL(6)
python3 test_vec_opt_pool_100combos.py
# Expected: < 2 min (vs 4 min non-VEC POOL)
```

#### D.3: Full Phase 1 Smoke Test

```bash
# Test 3: Full Phase 1 (400 combos) on MNQ 15m
python3 phase1_signal_independent_pool_vec_opt.py \
  --asset MNQ --timeframe 15m --comb 002 --workers 6
# Expected: < 8 min, all 400 combos pass, top-10 PF > 1.0
```

#### D.4: Equivalence Verification

```bash
# Test 4: Compare VEC vs non-VEC results
python3 test_vec_optimized_equivalence.py
# Expected: 100% identical results (trades, PF, max_dd)
```

#### Deliverable
- `docs/vec_opt_benchmark_results.md` with all timings
- Equivalence test passing for ALL combos

---

### PHASE E: Build Orchestrator Script (30 min)

`run_phases_1_to_5_tank_VEC_POOL_OPTIMIZED.sh`:

```bash
#!/bin/bash
# TANK VEC+POOL OPTIMIZED — All 5 phases with vectorized indicators
set -e

echo "==============================================="
echo "TANK VEC+POOL OPTIMIZED — Phases 1-5"
echo "==============================================="

cd ~/mogalef-systems-lab/mgf-control

PIPELINES=(
  "MNQ:15m:001"  # Note: keep MNQ 001 to test if VEC fixes the 0-trades issue
  "MNQ:15m:002"
  "ES:5m:001"
  "ES:5m:002"
  "FDAX:5m:001"
  "FDAX:5m:002"
  "FDAX:10m:001"
  "FDAX:10m:002"
  "MNQ:5m:001"
  "MNQ:5m:002"
  "ES:10m:002"
  "MNQ:10m:001"
)

for PIPELINE in "${PIPELINES[@]}"; do
  IFS=':' read ASSET TF COMB <<< "$PIPELINE"
  LOG="logs/tank_VEC_OPT_${ASSET}_${TF}_${COMB}.log"
  mkdir -p logs

  (
    echo "[TANK VEC-OPT] Starting $ASSET $TF $COMB" | tee "$LOG"

    # Phase 1 VEC+POOL
    python3 phase1_signal_independent_pool_vec_opt.py \
      --asset "$ASSET" --timeframe "$TF" --comb "$COMB" \
      --out ./phase1_results --workers 6 >> "$LOG" 2>&1

    # Phase 2a VEC+POOL
    python3 phase2a_horaire_independent_pool_vec_opt.py \
      --asset "$ASSET" --timeframe "$TF" --comb "$COMB" \
      --out ./phase2a_results --workers 6 >> "$LOG" 2>&1

    # Phase 2b VEC+POOL
    python3 phase2b_regime_independent_pool_vec_opt.py \
      --asset "$ASSET" --timeframe "$TF" --comb "$COMB" \
      --out ./phase2b_results --workers 6 >> "$LOG" 2>&1

    # Phase 3 VEC+POOL
    python3 phase3_exits_independent_pool_vec_opt.py \
      --asset "$ASSET" --timeframe "$TF" --comb "$COMB" \
      --out ./phase3_results --workers 6 >> "$LOG" 2>&1

    # Phase 4 VEC+POOL
    python3 phase4_stops_independent_pool_vec_opt.py \
      --asset "$ASSET" --timeframe "$TF" --comb "$COMB" \
      --out ./phase4_results --workers 6 >> "$LOG" 2>&1

    # Phase 5 VEC+POOL
    python3 phase5_combine_filters_vec_opt.py \
      --asset "$ASSET" --timeframe "$TF" --comb "$COMB" \
      --phase1-dir ./phase1_results --phase2a-dir ./phase2a_results \
      --phase2b-dir ./phase2b_results --phase3-dir ./phase3_results \
      --phase4-dir ./phase4_results --out ./phase5_results \
      --workers 6 >> "$LOG" 2>&1

    echo "[TANK VEC-OPT OK] $ASSET $TF $COMB" | tee -a "$LOG"
  ) &

  # Limit to 2 parallel pipelines (8 cores, POOL(6) each)
  if (( $(jobs -r -p | wc -l) >= 2 )); then
    wait -n
  fi
done

wait
echo "[TANK] All 12 pipelines complete (VEC+POOL OPTIMIZED)"
```

#### Deliverable
- `mgf-control/run_phases_1_to_5_tank_VEC_POOL_OPTIMIZED.sh`

---

### PHASE F: Deployment (30 min)

#### Pre-Deployment Checklist
- [ ] All VEC strategies pass equivalence tests
- [ ] Local benchmark shows >2x speedup for Phase 1
- [ ] Smoke test on MNQ 15m completes < 8 min
- [ ] All scripts pushed to GitHub
- [ ] BO continues running undisturbed

#### Deployment Steps
1. **Sync TANK code:**
   ```bash
   ssh tank "cd ~/mogalef-systems-lab && git fetch origin && git reset --hard origin/main"
   ```

2. **Clean previous results:**
   ```bash
   ssh tank "rm -rf ~/mogalef-systems-lab/mgf-control/phase*_results/*.json"
   ```

3. **Launch optimized run:**
   ```bash
   ssh tank "cd ~/mogalef-systems-lab/mgf-control && \
     nohup bash run_phases_1_to_5_tank_VEC_POOL_OPTIMIZED.sh \
       > tank_vec_opt_$(date +%Y%m%d_%H%M%S).log 2>&1 &"
   ```

4. **Monitor (5 cycles, 10 min intervals):**
   - Cycle 1: Process count, log tail
   - Cycle 2: First Phase 1 completing?
   - Cycle 3: Phase 1 outputs valid?
   - Cycle 4: Phase 2-3 progress?
   - Cycle 5: Overall ETA?

---

## Expected Performance

### Phase 1 (400 combos)
| Method | Time | Notes |
|--------|------|-------|
| Sequential non-VEC | 62 min | 9.3s/combo × 400 |
| POOL(6) non-VEC | 10-12 min | Current TANK |
| POOL(6) + VEC OPT | **3-4 min** | Target |

### Total Phases 1-5 per Pipeline
| Method | Time |
|--------|------|
| Sequential non-VEC | ~75 min |
| POOL(6) non-VEC | ~25-30 min |
| POOL(6) + VEC OPT | **~12-15 min** |

### TANK Total (12 pipelines, 2 parallel)
- Current (POOL only): ~3-4 hours
- Target (VEC+POOL OPT): **~1.5-2 hours**

---

## Pending Issues (Document, Don't Fix Now)

### Issue 1: MNQ 15m COMB_001 Returns 0 Trades in Phase 1 POOL
- **Symptom:** Phase 1 returns `[]` for COMB_001 (works fine for COMB_002)
- **Affected:** Both BO and TANK
- **Confirmed:** Direct test (no POOL) generates 3500+ trades
- **Hypothesis:** Pool worker exception silently caught, real error not logged
- **Action TODO (after VEC+POOL deployment):**
  - Add detailed exception logging in worker
  - Test if VEC version has same issue
  - If yes: investigate Pool serialization of Comb001TrendStrategy
  - If no: VEC fix this issue indirectly

### Issue 2: Memory Usage with POOL(6) + VEC
- VEC pre-calculates indicators as numpy arrays
- 6 workers × ~50MB indicator arrays = ~300MB extra
- Should be fine on 8-core machine with 16GB+ RAM
- Monitor during smoke test

---

## Success Criteria

✅ VEC+POOL completes Phase 1 in < 5 min (vs 10-12 min POOL only)
✅ Results match non-VEC version (100% identical trades and PF)
✅ All 12 pipelines complete in < 3 hours total
✅ MNQ 15m COMB_001 either succeeds OR error properly logged

---

## Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| A: Analysis | 1-2h | 2h |
| B: Build VEC strategies | 3-4h | 6h |
| C: Phase scripts | 2h | 8h |
| D: Local testing | 2-3h | 11h |
| E: Orchestrator | 30min | 11.5h |
| F: Deployment | 30min | 12h |

**Total implementation:** ~12 hours
**TANK execution after deployment:** ~1.5-2 hours
**Grand total:** ~14 hours from now to having results

---

## Files Created/Modified

### New Files
- `mgf-control/COMB_001_TREND_V1_vec_optimized.py`
- `mgf-control/COMB_002_IMPULSE_V2_vec_optimized.py`
- `mgf-control/test_vec_optimized_equivalence.py`
- `mgf-control/test_vec_opt_single_combo.py`
- `mgf-control/test_vec_opt_pool_100combos.py`
- `mgf-control/phase1_signal_independent_pool_vec_opt.py`
- `mgf-control/phase2a_horaire_independent_pool_vec_opt.py`
- `mgf-control/phase2b_regime_independent_pool_vec_opt.py`
- `mgf-control/phase3_exits_independent_pool_vec_opt.py`
- `mgf-control/phase4_stops_independent_pool_vec_opt.py`
- `mgf-control/phase5_combine_filters_vec_opt.py` (or update existing)
- `mgf-control/run_phases_1_to_5_tank_VEC_POOL_OPTIMIZED.sh`
- `docs/profiling_results.md`
- `docs/vec_opt_benchmark_results.md`

### Existing Files (Untouched)
- `phase1_signal_independent_pool.py` (current TANK script)
- `COMB_001_TREND_V1.py` (current strategy)
- `COMB_002_IMPULSE_V2_adaptive.py` (current strategy)

### To Deprecate (After VEC OPT Validated)
- `COMB_001_TREND_V1_vectorized.py` (slower, replaced by vec_optimized)

---

## Notes

- **BO continues running** during this implementation (no disruption)
- **TANK is stopped** waiting for VEC+POOL deployment
- **Implementation can be interrupted** between phases without losing progress
- **Each phase deliverable is testable** independently before proceeding

---

## Next Action

1. ✅ TANK stopped (DONE)
2. ✅ This plan documented (DONE — you are reading it)
3. ⏭️  User approval to proceed with PHASE A (Analysis)
4. ⏭️  Implementation following plan above

