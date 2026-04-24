# COMB_001 Trend Trading - Walk-Forward Backtest Protocol

## 1. Purpose

This protocol defines the **rigorous, reproducible methodology** for validating COMB_001 Trend Trading Version A through walk-forward testing. It ensures:

- ✓ No lookahead bias (unseen data validation)
- ✓ Separation of training and validation sets
- ✓ Objective measurement of overfitting risk
- ✓ Professional robustness validation
- ✓ Methodological compliance with Mogalef framework

---

## 2. Data Requirements

### 2.1 Minimum Data Length

- **Global minimum**: 2 years (sufficient for multiple market regimes)
- **Recommended**: 3-4 years for statistical robustness
- **Phase A (training) minimum**: 12-18 months
- **Phase B (validation) minimum**: 6-12 months (must be truly different regime period)

### 2.2 Data Quality

- **No gaps**: Continuous OHLC bars (5-minute recommended for liquid instruments)
- **Source consistency**: Same data provider throughout (avoid stitching different sources)
- **Currency/adjustment**: Unadjusted prices (futures) or split-adjusted (equities)
- **Regime similarity**: Both Phase A and Phase B must be from same market type/instrument

### 2.3 Data Preparation

1. Load full 2+ year dataset into memory
2. Verify data integrity (no NaN, no gaps, proper timestamp ordering)
3. **Split chronologically** (NOT randomly):
   - **Phase A**: First 60% of data (training set)
   - **Phase B**: Last 40% of data (validation set)
4. Document split point (exact date/timestamp)
5. Confirm no cross-contamination (Phase A timestamps < Phase B timestamps)

### 2.4 Example Data Split

```
Full data: 2022-01-01 to 2024-12-31 (3 years = ~750 trading days)

Phase A (Training):   2022-01-01 to 2023-06-30 (~450 days)
Phase B (Validation): 2023-07-01 to 2024-12-31 (~300 days)

Split ratio: 60% / 40% ✓
```

---

## 3. Baseline Backtest (Phase A + B with Default Parameters)

### 3.1 Objective

Establish a reference point before any optimization. This baseline confirms:
- Code executes without errors
- Components integrate correctly
- Metrics are calculable
- Phase B performance establishes robustness expectation

### 3.2 Execution Steps

**Step 1: Run Phase A (Training Set)**

```
Strategy: COMB_001_TREND_V1
Parameters: All defaults (from COMB_001_TREND_V1_params.txt)
Data: Phase A only (first 60%)
Output: 
  - COMB_001_TREND_trades_phase_A.csv
  - COMB_001_TREND_summary_phase_A.json
```

**Record Phase A Metrics**:
- Trade count
- Wins / Losses
- Profit Factor (PF)
- Win Rate (WR)
- Max Drawdown (DD)
- Avg Win / Avg Loss
- Exit reason breakdown
- Equity curve (cumulative PnL)

**Step 2: Run Phase B (Validation Set) with Phase A Parameters**

```
Strategy: COMB_001_TREND_V1
Parameters: SAME as Phase A (use defaults, NO optimization on Phase B)
Data: Phase B only (last 40%)
Output:
  - COMB_001_TREND_trades_phase_B.csv
  - COMB_001_TREND_summary_phase_B.json
```

**Record Phase B Metrics** (same as Phase A).

### 3.3 Robustness Check

Calculate **robustness ratio**:
```
Robustness = Phase_B_PF / Phase_A_PF
```

**Interpretation**:
- `Robustness >= 0.80` ✓ Good (default params generalize)
- `Robustness 0.60-0.80` ⚠ Moderate overfitting; Phase 1-4 optimization may help
- `Robustness < 0.60` ✗ Severe overfitting; revise strategy design

**Action**:
- If robustness ≥ 0.80: Proceed to Phase 1 optimization
- If robustness < 0.80: Investigate baseline design (filter may be too tight, targets too aggressive)

---

## 4. Optimization Phases (1-4)

### 4.1 General Optimization Protocol

**CRITICAL CONSTRAINT**: Never optimize multiple components simultaneously.

**Phase Structure**:
1. Lock all previous phase results
2. Lock non-optimization components to defaults
3. Vary ONE component's parameters in isolation
4. Test each combination on Phase A
5. Validate best combo on Phase B
6. Record optimization log

### 4.2 Phase 1: Signal Component Optimization

**Duration**: 10-12 hours

**Component**: EL_STPMT_DIV (divergence detection)

**Parameters to Vary**:
- `stpmt_smooth_h`: [1, 2, 3, 4, 5]
- `stpmt_smooth_b`: [1, 2, 3, 4, 5]
- `stpmt_distance_max_h`: [50, 100, 150, 200, 300]
- `stpmt_distance_max_l`: [50, 100, 150, 200, 300]

**Parameters to Lock**:
- Contexto: All at defaults
- Exits: All at defaults
- Stops: All at defaults

**Test Strategy**:
1. Create 5×5×5×5 = 625 parameter combos (computationally feasible)
2. Run each combo on Phase A
3. Record PF, WR, DD for each
4. Sort by PF (descending)
5. Take top 5-10 combos
6. Test each on Phase B
7. Select combo with best Phase B robustness (not necessarily highest Phase A PF)

**Documentation**: Create `Phase1_OptimizationLog.txt`
```
Combo | smooth_h | smooth_b | dist_max_h | dist_max_l | Phase_A_PF | Phase_A_WR | Phase_B_PF | Phase_B_WR | Selected
------|----------|----------|------------|------------|------------|------------|------------|------------|----------
1     | 2        | 2        | 200        | 200        | 1.45       | 52.1       | 1.31       | 49.2       | BASELINE
2     | 3        | 2        | 200        | 200        | 1.58       | 54.3       | 1.28       | 48.1       |
3     | 2        | 3        | 200        | 200        | 1.52       | 51.8       | 1.35       | 50.1       | ✓ BEST
...
```

**Output**: Best Phase 1 parameters locked for Phase 2

---

### 4.3 Phase 2: Contexto Filters Optimization

**Duration**: 12-16 hours

**Components**: Trend Filter + Horaire + Volatility

**Parameters to Vary**:
- `trend_r2`: [60, 75, 90, 120]
- `trend_r3`: [100, 120, 150, 200]
- `horaire_allowed_hours_utc`: [[], [9-15], [10-14], [8-16]]
- `volatility_atr_min`: [0.0, 2.0, 5.0, 10.0]
- `volatility_atr_max`: [100, 200, 300, 500, 1000]

**Parameters to Lock**:
- Signal: Phase 1 best combo
- Exits: All at defaults
- Stops: All at defaults

**Test Strategy**:
1. Create 4×4×4×4×5 = 1,280 combos
2. Run each on Phase A
3. Sort by Phase B robustness (not Phase A PF; this prevents overfitting)
4. Select best that improves or maintains Phase A PF while improving Phase B

**Documentation**: Create `Phase2_OptimizationLog.txt` (same format as Phase 1)

**Output**: Best Phase 2 parameters locked for Phase 3

---

### 4.4 Phase 3: Exits Optimization

**Duration**: 6-8 hours

**Components**: Profit Target + TimeStop

**Parameters to Vary**:
- `target_atr_multiplier`: [5.0, 7.0, 10.0, 15.0, 20.0]
- `timescan_bars`: [20, 25, 30, 40, 50]

**Parameters to Lock**:
- Signal: Phase 1 best
- Contexto: Phase 2 best
- Stops: All at defaults

**Test Strategy**:
1. Create 5×5 = 25 combos
2. Run each on Phase A
3. Validate on Phase B
4. Select best Phase B combo (prefer balanced exits: mix of targets + stops + opposite signals)

**Documentation**: Create `Phase3_OptimizationLog.txt`

**Output**: Best Phase 3 parameters locked for Phase 4

---

### 4.5 Phase 4: Stop Inteligente Optimization

**Duration**: 12-14 hours

**Component**: Stop Inteligente (volatility-adaptive trailing stop)

**Parameters to Vary**:
- `stop_intelligent_quality`: [1, 2, 3]
- `stop_intelligent_recent_volat`: [1, 2, 3, 5]
- `stop_intelligent_ref_volat`: [10, 15, 20, 30]
- `stop_intelligent_coef_volat`: [3.0, 4.0, 5.0, 6.0, 7.0]

**Parameters to Lock**:
- Signal: Phase 1 best
- Contexto: Phase 2 best
- Exits: Phase 3 best

**Test Strategy**:
1. Create 3×4×4×5 = 240 combos
2. Run each on Phase A
3. Validate on Phase B
4. Select combo that reduces average loss while maintaining win rate

**Documentation**: Create `Phase4_OptimizationLog.txt`

**Output**: Best Phase 4 parameters (final optimized strategy)

---

### 4.6 Optimization Log Format

Each phase should produce a standardized log:

```
PHASE 1: SIGNAL OPTIMIZATION
==============================
Start Date: 2026-04-20
Parameter Range: smooth_h=[1-5], smooth_b=[1-5], distance_max=[50-300]
Total Combos: 625
Time Elapsed: 10.5 hours

Top 10 Combos (sorted by Phase B Robustness):
---
Rank | Params | Phase A PF | Phase A WR | Phase B PF | Phase B WR | Robustness | Notes
---
1    | (3,2,200,200) | 1.58 | 54.3 | 1.35 | 50.1 | 0.854 | ✓ SELECTED: Best Phase B balance
2    | (2,3,200,200) | 1.52 | 51.8 | 1.34 | 49.8 | 0.882 | Slightly higher robustness but lower Phase A
3    | (3,3,150,200) | 1.63 | 55.1 | 1.32 | 49.5 | 0.810 | Overfitted to Phase A
...

FINAL PHASE 1 PARAMS:
  stpmt_smooth_h = 3
  stpmt_smooth_b = 2
  stpmt_distance_max_h = 200
  stpmt_distance_max_l = 200

Recommendation: Proceed to Phase 2 with these params locked
```

---

## 5. Final Validation (Phase 5)

### 5.1 Combine and Validate

**Step 1**: Assemble final parameters from Phases 1-4

```
Final Params = Phase_1_best + Phase_2_best + Phase_3_best + Phase_4_best
```

**Step 2**: Run final strategy on combined data (Phase A + Phase B)

```
Strategy: COMB_001_TREND_V1
Parameters: Final combined params
Data: Full dataset (Phase A + Phase B)
Output:
  - COMB_001_TREND_trades_final.csv
  - COMB_001_TREND_summary_final.json
```

**Step 3**: Compare final Phase A vs Phase B (with optimized params)

```
Phase A (training with final params):  PF = ?, WR = ?, DD = ?
Phase B (validation with final params): PF = ?, WR = ?, DD = ?
Final Robustness = Phase_B_PF / Phase_A_PF = ?
```

**Decision**:
- If robustness ≥ 0.80: ✓ Strategy is robust, proceed to capital planning
- If robustness < 0.80: ⚠ Over-optimized; revisit Phase 1-2 with tighter constraints

### 5.2 Forward Testing (Optional, if data available)

If a completely unseen 3+ month dataset exists from the same market regime:

**Step 4**: Run final strategy on Phase C (forward test)

```
Strategy: COMB_001_TREND_V1
Parameters: Final combined params (NO re-optimization)
Data: Phase C (completely unseen, future period)
Output:
  - COMB_001_TREND_trades_phase_C.csv
  - COMB_001_TREND_summary_phase_C.json
```

**Validation**:
```
Phase_C_PF should be similar to Phase B (±10%)
Phase_C_DD should not exceed Phase A DD by >50%
Trade count should be reasonable for period length
```

---

## 6. Success Criteria

### 6.1 In-Sample (Phase A) Targets

These are MINIMUM thresholds for a viable trading strategy:

| Metric | Target | Rationale |
|--------|--------|-----------|
| Profit Factor | ≥ 1.5 | Gross wins / gross losses |
| Win Rate | ≥ 50% | At least half trades profit |
| Max Drawdown | ≤ 30% | Max loss from peak |
| Trade Count | ≥ 20 | Sufficient sample (min 20 trades) |
| Avg Win / Avg Loss | ≥ 1.0 | Win size ≥ loss size |

### 6.2 Out-of-Sample (Phase B) Targets

These are MORE CONSERVATIVE (expect degradation):

| Metric | Target | Rationale |
|--------|--------|-----------|
| Profit Factor | ≥ 1.3 | At least 80% of Phase A |
| Win Rate | ≥ 45% | Slightly lower out-of-sample |
| Max Drawdown | ≤ 35% | More conservative bound |
| Trade Count | ≥ 10 | Minimum statistical sample |

### 6.3 Robustness Check

```
Robustness Ratio = Phase_B_PF / Phase_A_PF

✓ Excellent:    >= 0.90 (minimal overfitting)
✓ Good:         >= 0.80 (acceptable, generalizes well)
⚠ Moderate:    0.60-0.80 (some overfitting, may still be viable)
✗ Poor:        < 0.60 (severe overfitting, do not proceed)
```

### 6.4 Exit Reason Distribution

The strategy should NOT rely on ONE exit type too heavily:

```
Ideal:
  Stop hits:        30-40%
  Target hits:      30-40%
  Opposite signal:  10-20%
  TimeStop:         5-15%

Red flags:
  Stop hits > 60%:  Targets too aggressive, risk/reward wrong
  Target hits > 60%: Targets too loose, giving back profits
  Opposite signal < 5%: Filter too tight, missing reversals
```

---

## 7. Python/NT8 Reconciliation

### 7.1 Purpose

Verify that NinjaScript C# port produces identical results to Python (accounting for floating-point tolerance).

### 7.2 Reconciliation Steps

**Step 1**: Export Python trades to CSV
```
COMB_001_TREND_V1.py --csv-path data.csv --trades-out python_trades.csv
```

**Step 2**: Run NT8 strategy on same data
```
NinjaScript COMB001_TREND.cs (backtest mode)
Export trades: NT8_trades.csv
```

**Step 3**: Compare trade-by-trade

```python
python_trades = load_csv("python_trades.csv")
nt8_trades = load_csv("NT8_trades.csv")

for i in range(len(python_trades)):
    py = python_trades[i]
    nt = nt8_trades[i]
    
    # Check entry/exit match
    assert py.entry_index == nt.entry_index, "Entry index mismatch"
    assert py.exit_index == nt.exit_index, "Exit index mismatch"
    assert abs(py.entry_price - nt.entry_price) < 0.00001, "Entry price mismatch"
    assert abs(py.exit_price - nt.exit_price) < 0.00001, "Exit price mismatch"
    assert abs(py.pnl_points - nt.pnl_points) < 0.01, "PnL mismatch"
    assert py.exit_reason == nt.exit_reason, "Exit reason mismatch"
```

### 7.3 Tolerance Levels

| Property | Tolerance | Reason |
|----------|-----------|--------|
| Entry/exit index | ±0 bars | Must be exact (timing) |
| Entry/exit price | ±0.00001 | Floating-point rounding |
| PnL points | ±0.01 | Rounding accumulated over trade |
| Exit reason | Exact match | Logic must be identical |
| Trade count | ±1 | Edge case handling (end of data) |

### 7.4 Reconciliation Output

Document differences in `Reconciliation_Report.md`:
```
# Python vs NT8 Reconciliation Report

## Summary
- Python trades: 47
- NT8 trades: 47
- Reconciliation: ✓ PASS

## Trade-by-Trade Verification
- Entry prices match: ✓ All 47/47
- Exit prices match: ✓ All 47/47
- Exit reasons match: ✓ All 47/47
- PnL points match: ✓ All 47/47 (tolerance ±0.01)

## Metrics Comparison
| Metric | Python | NT8 | Diff |
|--------|--------|-----|------|
| Equity Points | 1245.53 | 1245.54 | +0.01 |
| Win Rate | 51.1% | 51.1% | 0% |
| Profit Factor | 1.42 | 1.42 | 0% |
| Max DD | 425.30 | 425.32 | +0.02 |

## Conclusion
NT8 implementation is **VERIFIED** against Python baseline.
Both can be used for live trading with identical logic.
```

---

## 8. Capital Planning

### 8.1 Minimum Capital Calculation

**Formula**:
```
Minimum Capital = Max_Drawdown × 10
```

**Rationale**: 
- Max DD = largest peak-to-trough loss observed in backtest
- ×10 multiplier = margin + buffer for out-of-sample draws

**Example**:
```
Phase B Max DD = 2,450 points
Min Capital = 2,450 × 10 = 24,500 (in account currency)
```

### 8.2 Recommended Account Size

**Formula**:
```
Recommended Account Size = Minimum Capital × 2
```

**Rationale**:
- 2× buffer accounts for:
  - Margin requirement (typically 50% of notional)
  - Slippage and commissions
  - Unexpected regime changes
  - Multiple system diversification

**Example**:
```
Min Capital = 24,500
Recommended = 24,500 × 2 = 49,000
```

### 8.3 Multi-System Recommendation

**Mogalef Safety Framework**: Distribute risk across 3-4 independent systems:

```
Total Account = 50,000
System A (COMB_001_TREND on ES): 15,000
System B (COMB_001_TREND on NQ): 15,000
System C (Variant on GC):          15,000
Reserve (buffer):                   5,000
---
Total:                             50,000
```

**Benefits**:
- ✓ Reduces correlation risk
- ✓ Ensures stability if one system underperforms
- ✓ Allows for regime changes in subsets
- ✓ Professional risk distribution

---

## 9. Performance Reporting

### 9.1 Standard Report Template

Create `COMB_001_TREND_Final_Validation_Report.md` with:

```markdown
# COMB_001 Trend Trading - Final Validation Report

## Executive Summary
- Strategy: COMB_001_TREND_V1
- Test Period: 2022-01-01 to 2024-12-31
- Data Source: [instrument, timeframe, provider]
- Status: [PASSED / NEEDS REVISION]

## Phase A (Training) Results
- Trade Count: 47
- Wins/Losses: 24/23
- Equity Points: +1,245.53
- Profit Factor: 1.42
- Win Rate: 51.1%
- Max Drawdown: 425.30 points
- Avg Win: 58.20
- Avg Loss: 52.15

## Phase B (Validation) Results
- Trade Count: 31
- Wins/Losses: 16/15
- Equity Points: +893.42
- Profit Factor: 1.31
- Win Rate: 51.6%
- Max Drawdown: 382.15 points
- Avg Win: 59.55
- Avg Loss: 54.20

## Robustness Analysis
- Phase A PF: 1.42
- Phase B PF: 1.31
- Robustness Ratio: 0.92 ✓ EXCELLENT

## Exit Reason Breakdown
| Reason | Phase A | Phase B |
|--------|---------|---------|
| Stop | 18 (38%) | 12 (39%) |
| Target | 15 (32%) | 10 (32%) |
| Opposite Signal | 9 (19%) | 6 (19%) |
| TimeStop | 5 (11%) | 3 (10%) |

## Capital Requirements
- Max Drawdown: 425.30 points
- Min Capital = 425.30 × 10 = 4,253 (account currency units)
- Recommended = 4,253 × 2 = 8,506
- Multi-System Allocation (3 systems): 8,506 × 3 = 25,518 total

## Optimization Details
- Phase 1 (Signal): smooth_h=3, smooth_b=2, distance_max=200
- Phase 2 (Contexto): trend_r2=90, trend_r3=150, horaire=9-15
- Phase 3 (Exits): target_atr_multiplier=10.0, timescan_bars=30
- Phase 4 (Stops): quality=2, recent_volat=2, ref_volat=20, coef_volat=5.0

## Approval Status
- ✓ In-sample targets: PASSED
- ✓ Out-of-sample robustness: PASSED
- ✓ Python/NT8 reconciliation: PASSED
- ✓ Capital planning: COMPLETED

**RECOMMENDATION**: Strategy is ready for live trading on ES 5-minute with 8,506+ capital.
Recommended: Deploy with 2 systems for diversification.
```

---

## 10. Checklist for Protocol Compliance

Use this checklist to verify protocol adherence:

```
Data Preparation
  ☐ Full 2+ years of data loaded
  ☐ Data quality verified (no gaps, proper format)
  ☐ Phase A/B split at 60/40 chronologically
  ☐ No cross-contamination (A < B timestamps)

Baseline
  ☐ Phase A run with defaults completed
  ☐ Phase B run with Phase A params completed
  ☐ Robustness ratio calculated
  ☐ Baseline log documented

Phase 1 (Signal)
  ☐ Contexto/Exits/Stops locked to defaults
  ☐ Signal params varied in isolation
  ☐ Best combo validated on Phase B
  ☐ Phase 1 log documented

Phase 2 (Contexto)
  ☐ Signal locked to Phase 1 best
  ☐ Contexto params varied in isolation
  ☐ Best combo validated on Phase B
  ☐ Phase 2 log documented

Phase 3 (Exits)
  ☐ Signal/Contexto locked to Phase 1-2 best
  ☐ Exit params varied in isolation
  ☐ Best combo validated on Phase B
  ☐ Phase 3 log documented

Phase 4 (Stops)
  ☐ Signal/Contexto/Exits locked to Phase 1-3 best
  ☐ Stop params varied in isolation
  ☐ Best combo validated on Phase B
  ☐ Phase 4 log documented

Final Validation
  ☐ Combined final params assembled
  ☐ Final strategy run on full dataset
  ☐ Robustness ratio confirmed ≥ 0.80
  ☐ Capital planning completed
  ☐ Final validation report generated

Python/NT8 Reconciliation
  ☐ NT8 code compiles without errors
  ☐ Trade-by-trade comparison performed
  ☐ All metrics match within tolerance
  ☐ Reconciliation report signed off

Ready for Deployment?
  ☐ Phase A PF ≥ 1.5
  ☐ Phase B PF ≥ 1.3
  ☐ Robustness ≥ 0.80
  ☐ Trade count adequate (Phase A ≥ 20, Phase B ≥ 10)
  ☐ Exit distribution balanced (no single reason > 60%)
  ☐ Documentation complete
```

---

## 11. Notes and Best Practices

### 11.1 Avoiding Overfitting

**Red Flags** (indicates over-optimization):
- Phase A PF drops sharply between optimization phases
- Phase B robustness < 0.80 (indicates Phase A overfitting)
- Optimization log shows many parameters changed simultaneously
- Exit reasons become heavily skewed to one type

**Prevention**:
- Lock previous phases rigorously
- Validate each combo on Phase B before moving forward
- Sort by Phase B robustness (not Phase A PF)
- Limit combo space (don't test 10,000 possibilities)

### 11.2 Handling Insufficient Trade Count

If Phase B has < 10 trades:
- ⚠ Statistical significance questionable
- Consider:
  1. Extend Phase B window (get more data)
  2. Reduce Phase A window if possible (give more data to Phase B)
  3. Loosen filters (Horaire, Volatility) to generate more signals
  4. Accept reduced validation power (document clearly)

### 11.3 Regime Changes

If Phase B shows significantly different behavior:
- Investigate regime (market structure, volatility, trend)
- Check if Phase A/Phase B are from same market type
- Example: Bull market (A) vs Bear market (B) may require different params
- **Solution**: Split data by regime, optimize separately for each

### 11.4 Handling Negative Expectancy

If even defaults produce Phase B PF < 1.0:
- Strategy is not profitable on unseen data
- **Do NOT proceed** with optimization
- Revisit strategy design:
  1. Signal component too weak?
  2. Filters too aggressive (blocking good trades)?
  3. Exits/stops wrong (giving back profits)?
  4. Consider COMB_001_TREND_V2 or alternative design

---

## Appendix: Sample Execution Commands

### Python Backtest (Phase A)

```bash
cd /path/to/mogalef-systems-lab/mgf-control
python COMB_001_TREND_V1.py \
  /data/phase_A.csv \
  --trades-out phase_A_trades.csv \
  --summary-out phase_A_summary.json
```

### Python Backtest (Phase B)

```bash
python COMB_001_TREND_V1.py \
  /data/phase_B.csv \
  --trades-out phase_B_trades.csv \
  --summary-out phase_B_summary.json
```

### Optimization Wrapper (Pseudo-Code)

```python
best_pf_b = 0
best_params = None

for smooth_h in [1, 2, 3, 4, 5]:
    for smooth_b in [1, 2, 3, 4, 5]:
        for dist_h in [50, 100, 150, 200, 300]:
            for dist_l in [50, 100, 150, 200, 300]:
                
                params = Comb001TrendParams(
                    stpmt_smooth_h=smooth_h,
                    stpmt_smooth_b=smooth_b,
                    stpmt_distance_max_h=dist_h,
                    stpmt_distance_max_l=dist_l,
                    # All other params = defaults or Phase 1-3 best
                )
                
                strategy = Comb001TrendStrategy(params)
                result_a = strategy.run(phase_a_rows)
                result_b = strategy.run(phase_b_rows)
                
                if result_b.profit_factor > best_pf_b:
                    best_pf_b = result_b.profit_factor
                    best_params = params
                    log(f"NEW BEST: {params} -> Phase B PF={best_pf_b:.2f}")

return best_params
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-20  
**Protocol Owner**: mogalef-systems-lab  
**Status**: Approved for implementation
