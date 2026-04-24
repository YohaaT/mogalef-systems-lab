# COMB_003 Breakout Trading - Baseline Walk-Forward Report

## Data Split Summary

| Metric | Value |
|--------|-------|
| Total rows | 671,281 |
| Phase A (training) | 402,768 rows |
| Phase B (validation) | 268,513 rows |

---

## Baseline Results (Default Parameters)

### Phase A (Training Set)

| Metric | Value |
|--------|-------|
| Trade Count | 3543 |
| Wins | 676 |
| Losses | 2867 |
| Win Rate | 19.08% |
| Equity Points | -3260.00 |
| Profit Factor | **0.9431** |
| Max Drawdown | 4820.00 pts |
| Avg Win | 80.00 pts |
| Avg Loss | -20.00 pts |

Exit breakdown: {'target': 676, 'stop': 2867}

---

### Phase B (Validation Set - UNSEEN DATA)

| Metric | Value |
|--------|-------|
| Trade Count | 2724 |
| Wins | 510 |
| Losses | 2214 |
| Win Rate | 18.72% |
| Equity Points | -3480.00 |
| Profit Factor | **0.9214** |
| Max Drawdown | 4140.00 pts |
| Avg Win | 80.00 pts |
| Avg Loss | -20.00 pts |

Exit breakdown: {'stop': 2214, 'target': 510}

---

## Robustness Analysis

```
Robustness Ratio = Phase_B_PF / Phase_A_PF
                = 0.9214 / 0.9431
                = 0.9770
                = 97.70%
```

**Status**: [PASS] ACCEPTABLE

---

## Key Differences vs COMB_001 and COMB_002

| Aspect | COMB_001 (Trend) | COMB_002 (Impulse) | COMB_003 (Breakout) |
|--------|------------------|-------------------|-------------------|
| Signal | STPMT divergence | STPMT divergence | Structural breakout |
| Filters | Trend + Horaire + Vol | Horaire + Vol | NeutralZone + Trend + Horaire |
| Target Type | 10 ATR | Scalping (3 ATR) | Fixed (60-80 pts) |
| TimeStop | 30 bars | 15 bars | None (target/stop only) |
| Stop Type | Stop Inteligente | SuperStop | Fixed stop (20 pts) |
| Risk/Reward | Variable | Variable | Fixed 1:4 |
| Market Regime | Trending | Any | Breakout/Structural |

---

## Interpretation

COMB_003 is designed for **breakout trading**, catching structural price movements with fixed risk/reward.
- Fixed stops reduce variability but cap maximum loss
- Fixed targets provide consistent exit points
- Neutral Zone filter helps avoid false breakouts in choppy zones
- Works best in markets with clear structural support/resistance

If robustness is low, optimization should focus on:
1. Signal quality (Phase 1: breakout lookback periods)
2. Filter selectivity (Phase 2: Neutral Zone + Trend parameters)
3. Risk/Reward calibration (Phase 3: stop/target sizing)

---

**Next Steps**: Phase 1 Optimization (Breakout signal parameters) if robustness < 0.80
