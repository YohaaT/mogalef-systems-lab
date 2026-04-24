# COMB_001 Trend Trading - Baseline Walk-Forward Report

## Data Split Summary

| Metric | Value |
|--------|-------|
| Total rows | 13,725 |
| Split point | Row 8,235 (60/40) |
| Phase A (training) | 8,235 rows - Feb 3 to Mar 18, 2026 |
| Phase B (validation) | 5,490 rows - Mar 18 to Apr 15, 2026 |

---

## Baseline Results (Default Parameters)

### Phase A (Training Set)

| Metric | Value |
|--------|-------|
| Trade Count | 47 |
| Wins | 12 |
| Losses | 35 |
| Win Rate | 25.53% |
| Equity Points | +502.50 |
| Profit Factor | **1.6395** |
| Max Drawdown | 422.00 pts |
| Avg Win | 107.35 pts |
| Avg Loss | 22.45 pts |

**Exit Breakdown**: Stop 74%, TimeStop 9%, Opposite Signal 15%, Target 2%

---

### Phase B (Validation Set - UNSEEN DATA)

| Metric | Value |
|--------|-------|
| Trade Count | 30 |
| Wins | 1 |
| Losses | 29 |
| Win Rate | 3.33% ⚠️ |
| Equity Points | **-889.50** ⚠️ |
| Profit Factor | **0.0681** ⚠️ |
| Max Drawdown | 918.75 pts ⚠️ |
| Avg Win | 65.00 pts |
| Avg Loss | 32.91 pts |

**Exit Breakdown**: Stop 97%, Opposite Signal 3%, Target 0%

---

## Robustness Analysis

```
Robustness Ratio = Phase_B_PF / Phase_A_PF
                = 0.0681 / 1.6395
                = 0.0416
                = 4.16%
```

### Status: ❌ SEVERE OVERFITTING DETECTED

| Criterion | Target | Phase A | Phase B | Status |
|-----------|--------|---------|---------|--------|
| Profit Factor | >=1.5 (A), >=1.3 (B) | 1.64 ✓ | 0.07 ✗ | FAILED |
| Win Rate | >=50% (A), >=45% (B) | 25.53% ✗ | 3.33% ✗ | FAILED |
| Max DD | <=30% (A), <=35% (B) | 422 pts | 918.75 pts | FAILED |
| Robustness | >=0.80 | — | 4.16% | FAILED |

---

## Root Cause Analysis

### Phase A vs Phase B Comparison

```
Phase A (Feb-Mar):   Trending market, lower DD, profitable
Phase B (Mar-Apr):   Ranging/choppy market, higher DD, mostly losses
```

**Key Observations**:
1. **Win Rate collapsed** 25.53% → 3.33% (10x drop)
2. **Profit Factor collapsed** 1.64 → 0.07 (23x drop)
3. **Max Drawdown doubled** 422 → 918.75 pts
4. **Regime change**: Phase B appears to be different market structure
   - Fewer tradeable setups
   - STPMT signals trapped in consolidation
   - Trend Filter blocking more trades
   - Opposite signal exits not triggering (0 target hits)

---

## Interpretation

### Baseline Is NOT Profitable

The default parameters produce:
- ✓ Good results on Phase A (training data)
- ✗ Terrible results on Phase B (unseen data)

**This is exactly what we expected** - default parameters are conservative and not optimized.

### Optimization is Critical

Phase 1-4 optimization MUST:
1. Improve Phase B robustness (current 4.16% is indefensible)
2. Adapt to different market regimes
3. Tighten/adjust filters for choppy markets
4. Increase target hit rate (currently 2-3%)

---

## Recommendation

**PROCEED TO PHASE 1 OPTIMIZATION**

The baseline establishes a starting point. Now we optimize:

1. **Phase 1**: Vary STPMT signal (smooth_h/b, distance_max)
   - Goal: Generate better quality signals, fewer false entries
   
2. **Phase 2**: Vary Contexto filters (trend, horaire, volatility)
   - Goal: Block choppy periods, let trends through
   
3. **Phase 3**: Vary Exits (ATR multiplier, TimeStop)
   - Goal: Increase target hits from 2% to 30%+
   
4. **Phase 4**: Vary Stop Inteligente
   - Goal: Reduce average loss, adapt to volatility

**Target after optimization**: Phase B PF >= 1.3 (robustness >= 0.80)

---

## Files Generated

- `phase_A_training.csv` - Phase A data
- `phase_B_validation.csv` - Phase B data  
- `baseline_phase_A_trades.csv` - All Phase A trades
- `baseline_phase_B_trades.csv` - All Phase B trades
- `baseline_phase_A_summary.json` - Phase A metrics
- `baseline_phase_B_summary.json` - Phase B metrics
- `BASELINE_WALKFORWARD_REPORT.md` - This report

---

**Status**: Ready for Phase 1 Optimization

**Next Action**: Run optimization Phase 1 (Signal component)
