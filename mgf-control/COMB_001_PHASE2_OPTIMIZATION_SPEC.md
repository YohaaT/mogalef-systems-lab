# COMB_001 Phase 2 Optimization - Contexto Filters Specification

## Overview

Phase 2 optimizes the **Contexto component** after Phase 1 Signal optimization is locked.

**Locked from Phase 1:**
- stpmt_smooth_h: Best value from Phase 1
- stpmt_smooth_b: Best value from Phase 1
- stpmt_distance_max_h: Best value from Phase 1
- stpmt_distance_max_l: Best value from Phase 1

**Varied in Phase 2:**
1. Trend Filter (R1, R2, R3 parameters)
2. Horaire (UTC hour restrictions)
3. Volatility (ATR bounds)

---

## 1. Trend Filter Optimization

### Current Defaults
- `trend_r1 = 1` (minimum repulse level)
- `trend_r2 = 90` (medium repulse level)
- `trend_r3 = 150` (strong repulse level)

### Why Optimize?
- Default values were chosen arbitrarily for YM futures
- Different markets/timeframes may need different thresholds
- Tighter filters → fewer false signals, fewer trades
- Looser filters → more trades, higher exposure

### Parameter Ranges for Testing

| Parameter | Min | Default | Max | Step | Rationale |
|-----------|-----|---------|-----|------|-----------|
| trend_r1 | 1 | 1 | 5 | 1 | Lower = more sensitive to price pressure |
| trend_r2 | 50 | 90 | 150 | 20 | Medium threshold for medium trends |
| trend_r3 | 100 | 150 | 300 | 50 | Higher = only strong trends pass |

**Total combinations:** 5 × 6 × 5 = **150 combos** (Trend Filter alone)

### Expected Behavior
- **tight (r1=1, r2=50, r3=100)**: More trades, higher noise
- **loose (r1=5, r2=150, r3=300)**: Fewer trades, cleaner signals
- **sweet spot**: Balance of trade count and quality

---

## 2. Horaire (Trading Hours) Optimization

### Current Default
- `horaire_allowed_hours_utc = [9, 10, 11, 12, 13, 14, 15]` (9 AM - 3 PM UTC = US market)

### Why Optimize?
- YM (Micro E-mini S&P 500) has different liquidity at different hours
- Some hours may have better trending, less noise
- Could optimize for specific market session (US, London, etc.)

### Parameter Ranges for Testing

Testing different hour blocks:

| Option | Hours (UTC) | Trading Session | Rationale |
|--------|-----------|-----------------|-----------|
| 0 | All hours (0-23) | 24-hour | Catches all moves |
| 1 | 9-15 | US Regular | Current default (9 AM - 3 PM ET) |
| 2 | 9-17 | US Extended | Include close hour (3 PM - 5 PM ET) |
| 3 | 8-16 | Pre-market + Regular | Catch early Asia/Europe spillover |
| 4 | 9-12 | Morning only | Highest volume window |
| 5 | 12-15 | Afternoon | Lower volume, cleaner moves |
| 6 | 14-18 | London + US afternoon | Cross-session |

**Total options:** 6 distinct hour profiles

### Expected Behavior
- All hours: Highest trade count, potential noise
- 9-15 (current): Balanced, proven
- 9-12: Peak volume, trending moves
- 14-18: Cross-session volatility

---

## 3. Volatility Filter Optimization

### Current Default
- `volatility_atr_min = 0.0` (no minimum floor)
- `volatility_atr_max = 500.0` (very loose ceiling)

### Why Optimize?
- ATR measures market volatility
- Too low ATR (tight, choppy) → more false signals
- Too high ATR (volatile) → risky, large swings
- Sweet spot depends on trading capital and risk tolerance

### Parameter Ranges for Testing

| Parameter | Min | Default | Max | Step | Rationale |
|-----------|-----|---------|-----|------|-----------|
| volatility_atr_min | 0 | 0 | 50 | 10 | Floor below which market is too choppy |
| volatility_atr_max | 100 | 500 | 500 | 50 | Ceiling above which market is too volatile |

**Test combinations:**

| atr_min | atr_max | Purpose |
|---------|---------|---------|
| 0 | 500 | No filter (current) |
| 10 | 500 | Minimum ATR to avoid chop |
| 0 | 200 | Exclude extreme volatility |
| 10 | 250 | Tight band (tight and volatile excluded) |
| 20 | 200 | Very selective |

**Total options:** 5 distinct volatility profiles

---

## Phase 2 Optimization Strategy

### Approach: Sequential or Grid?

**Option A: Grid Search (Recommended)**
- Test all combinations: Trend (150) × Horaire (6) × Volatility (5) = 4,500 combos
- Most comprehensive, but slow
- Divide into blocks: 9 blocks × 500 combos each

**Option B: Sequential Search**
- Optimize Trend Filter first (150 combos)
- Lock best, then optimize Horaire (6 options)
- Lock both, then optimize Volatility (5 options)
- Total: 150 + 6 + 5 = 161 combos (fast but may miss interactions)

**Recommended:** Option B (Sequential) for speed + good results

### Phase 2 Execution Plan

1. **Phase 2a: Trend Filter** (150 combos, ~10-15 min)
   - Lock Phase 1 best signal params
   - Vary trend_r1/r2/r3
   - Output: phase2a_best_params.json

2. **Phase 2b: Horaire** (6 tests, ~2-3 min)
   - Lock Phase 1 signal + Phase 2a best trend filter
   - Test 6 hour profiles
   - Output: phase2b_best_horaire.json

3. **Phase 2c: Volatility** (5 tests, ~2-3 min)
   - Lock Phase 1 signal + Phase 2a best trend + Phase 2b best horaire
   - Test 5 volatility profiles
   - Output: phase2c_best_volatility.json

**Total Phase 2 time:** ~15-20 minutes
**Total combos tested:** 161

---

## Success Criteria for Phase 2

After Phase 2 optimization, Phase B (unseen data) should show:

| Metric | Target |
|--------|--------|
| Profit Factor | ≥ 1.3 |
| Win Rate | ≥ 45% |
| Max Drawdown | ≤ 35% |
| Robustness | ≥ 0.80 |

If Phase 2 doesn't improve robustness significantly, may need to revisit Phase 1 signal quality or accept that this market regime is fundamentally different.

---

## Implementation Notes

### Causal Integrity
- All contexto checks happen on bar t (signal bar)
- Entry executes on bar t+1 (open)
- No lookahead

### Trend Filter Behavior
- Returns sentiment: "pass" or "block"
- "block" = skip trade, wait for better setup
- Higher r values = stricter = more blocks

### Horaire Behavior
- Hour extracted from timestamp_utc
- Simple list membership check
- No special handling for DST

### Volatility Behavior
- ATR calculated on each bar
- Filter: atr_min ≤ atr[i] ≤ atr_max
- Inclusive bounds

---

## Files to Create

1. `phase2_optimization_block_runner.py` - Runs Phase 2a (Trend Filter)
2. `phase2_horaire_tester.py` - Runs Phase 2b (Horaire)
3. `phase2_volatility_tester.py` - Runs Phase 2c (Volatility)
4. `phase2_combine_results.py` - Combines all Phase 2 results
5. `run_phase2_on_vps.sh` - VPS execution script

---

## Robustness Expectation

Typical progression (Example):
```
Phase 1 baseline:   Phase B PF = 1.04  (100% robustness)
After Phase 1 opt:  Phase B PF = 1.18  (achieves ~90% robustness vs Phase A)
After Phase 2 opt:  Phase B PF = 1.35  (achieves ~85% robustness, acceptable)
```

If Phase 2 results in LOWER Phase B PF, the filters were too restrictive (blocked good trades).

---

## Next: Phase 3 (Exits) and Phase 4 (Stops)

Once Phase 2 is complete:
- Phase 3: Optimize target_atr_multiplier (3-15 ATR) and timescan_bars (15-45)
- Phase 4: Optimize Stop Inteligente parameters (quality, volat_recent, volat_ref, coef)

Final backtest: Combine all Phase 1-4 best params on Phase A + Phase B for final validation.
