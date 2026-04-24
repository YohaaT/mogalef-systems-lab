# COMB_002 Impulse Trading - Baseline Walk-Forward Report

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
| Trade Count | 1962 |
| Wins | 904 |
| Losses | 1037 |
| Win Rate | 46.08% |
| Equity Points | 695.32 |
| Profit Factor | **1.0382** |
| Max Drawdown | 889.18 pts |
| Avg Win | 20.92 pts |
| Avg Loss | -17.56 pts |

Exit breakdown: {'timescan': 631, 'target': 486, 'stop': 734, 'opposite_signal': 111}

---

### Phase B (Validation Set - UNSEEN DATA)

| Metric | Value |
|--------|-------|
| Trade Count | 1372 |
| Wins | 635 |
| Losses | 717 |
| Win Rate | 46.28% |
| Equity Points | 577.25 |
| Profit Factor | **1.0415** |
| Max Drawdown | 853.32 pts |
| Avg Win | 22.79 pts |
| Avg Loss | -19.38 pts |

Exit breakdown: {'target': 360, 'timescan': 414, 'stop': 508, 'opposite_signal': 90}

---

## Robustness Analysis

```
Robustness Ratio = Phase_B_PF / Phase_A_PF
                = 1.0415 / 1.0382
                = 1.0032
                = 100.32%
```

**Status**: [PASS] ACCEPTABLE

---

## Key Differences vs COMB_001 Trend Trading

| Aspect | COMB_001 (Trend) | COMB_002 (Impulse) |
|--------|------------------|-------------------|
| Trend Filter | YES | NO (catches all impulses) |
| Target Type | 10 ATR (long-term) | Intelligent Scalping (short-term) |
| TimeStop | 30 bars | 15 bars |
| Stop Type | Stop Inteligente | SuperStop (tighter) |
| Market Regime | Trending only | Any regime |

---

## Interpretation

COMB_002 is designed for **impulse/scalping** trading, catching shorter moves in all market regimes.
If robustness is low, optimization should focus on:
1. Signal quality (Phase 1: smooth_h/b, distance_max)
2. Volatility filter tightness (Phase 2)
3. Scalping target sizing (Phase 3)

---

**Next Steps**: Phase 1 Optimization (Signal parameters) if robustness < 0.80
