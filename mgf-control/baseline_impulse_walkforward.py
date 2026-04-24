"""Baseline Walk-Forward Backtest for COMB_002 Impulse Trading (Version B)

Test default parameters on Phase A (training) and Phase B (unseen validation)
to establish robustness baseline before optimization.
"""

import csv
import json
from pathlib import Path
from COMB_002_IMPULSE_V1 import Comb002ImpulseStrategy, Comb002ImpulseParams, load_ohlc_csv

print("="*80)
print("COMB_002 IMPULSE TRADING - BASELINE WALK-FORWARD TEST")
print("="*80)

# Load Phase A and Phase B
print("\n[1] Loading data...")
phase_a_rows = load_ohlc_csv("YM_phase_A_clean.csv")
phase_b_rows = load_ohlc_csv("YM_phase_B_clean.csv")
print(f"Phase A: {len(phase_a_rows)} rows")
print(f"Phase B: {len(phase_b_rows)} rows")

# Test default parameters
print("\n[2] Testing default parameters...")
params = Comb002ImpulseParams()
strategy = Comb002ImpulseStrategy(params)

# Phase A (training)
print("\n[Phase A - Training]")
result_a = strategy.run(phase_a_rows)
print(f"  Trades: {len(result_a.trades)}")
print(f"  Wins: {result_a.wins}, Losses: {result_a.losses}")
print(f"  Win Rate: {result_a.win_rate:.2%}")
print(f"  Equity: {result_a.equity_points:.2f} pts")
print(f"  Profit Factor: {result_a.profit_factor:.4f}")
print(f"  Max Drawdown: {result_a.max_drawdown:.2f} pts")
if result_a.trades:
    print(f"  Avg Win: {result_a.avg_win:.2f} pts")
    print(f"  Avg Loss: {result_a.avg_loss:.2f} pts")
    print(f"  Exit breakdown: {result_a.exit_reason_breakdown}")

# Phase B (unseen validation)
print("\n[Phase B - Unseen Validation]")
result_b = strategy.run(phase_b_rows)
print(f"  Trades: {len(result_b.trades)}")
print(f"  Wins: {result_b.wins}, Losses: {result_b.losses}")
print(f"  Win Rate: {result_b.win_rate:.2%}")
print(f"  Equity: {result_b.equity_points:.2f} pts")
print(f"  Profit Factor: {result_b.profit_factor:.4f}")
print(f"  Max Drawdown: {result_b.max_drawdown:.2f} pts")
if result_b.trades:
    print(f"  Avg Win: {result_b.avg_win:.2f} pts")
    print(f"  Avg Loss: {result_b.avg_loss:.2f} pts")
    print(f"  Exit breakdown: {result_b.exit_reason_breakdown}")

# Robustness check
print("\n[3] Robustness Analysis")
robustness = result_b.profit_factor / result_a.profit_factor if result_a.profit_factor > 0 else 0
print(f"Robustness = Phase B PF / Phase A PF")
print(f"Robustness = {result_b.profit_factor:.4f} / {result_a.profit_factor:.4f}")
print(f"Robustness = {robustness:.2%}")

if robustness >= 0.80:
    print("[PASS] Robustness >= 80%")
else:
    print(f"[FAIL] Robustness < 80% (got {robustness:.2%})")

# Export results
print("\n[4] Exporting results...")

# Phase A trades
strategy.export_trades_csv(result_a.trades, "baseline_impulse_phase_a_trades.csv")
print("  [OK] baseline_impulse_phase_a_trades.csv")

# Phase B trades
strategy.export_trades_csv(result_b.trades, "baseline_impulse_phase_b_trades.csv")
print("  [OK] baseline_impulse_phase_b_trades.csv")

# Phase A summary
strategy.export_summary_json(result_a, "baseline_impulse_phase_a_summary.json")
print("  [OK] baseline_impulse_phase_a_summary.json")

# Phase B summary
strategy.export_summary_json(result_b, "baseline_impulse_phase_b_summary.json")
print("  [OK] baseline_impulse_phase_b_summary.json")

# Generate report
report = f"""# COMB_002 Impulse Trading - Baseline Walk-Forward Report

## Data Split Summary

| Metric | Value |
|--------|-------|
| Total rows | {len(phase_a_rows) + len(phase_b_rows):,} |
| Phase A (training) | {len(phase_a_rows):,} rows |
| Phase B (validation) | {len(phase_b_rows):,} rows |

---

## Baseline Results (Default Parameters)

### Phase A (Training Set)

| Metric | Value |
|--------|-------|
| Trade Count | {len(result_a.trades)} |
| Wins | {result_a.wins} |
| Losses | {result_a.losses} |
| Win Rate | {result_a.win_rate:.2%} |
| Equity Points | {result_a.equity_points:.2f} |
| Profit Factor | **{result_a.profit_factor:.4f}** |
| Max Drawdown | {result_a.max_drawdown:.2f} pts |
| Avg Win | {result_a.avg_win:.2f} pts |
| Avg Loss | {result_a.avg_loss:.2f} pts |

Exit breakdown: {result_a.exit_reason_breakdown}

---

### Phase B (Validation Set - UNSEEN DATA)

| Metric | Value |
|--------|-------|
| Trade Count | {len(result_b.trades)} |
| Wins | {result_b.wins} |
| Losses | {result_b.losses} |
| Win Rate | {result_b.win_rate:.2%} |
| Equity Points | {result_b.equity_points:.2f} |
| Profit Factor | **{result_b.profit_factor:.4f}** |
| Max Drawdown | {result_b.max_drawdown:.2f} pts |
| Avg Win | {result_b.avg_win:.2f} pts |
| Avg Loss | {result_b.avg_loss:.2f} pts |

Exit breakdown: {result_b.exit_reason_breakdown}

---

## Robustness Analysis

```
Robustness Ratio = Phase_B_PF / Phase_A_PF
                = {result_b.profit_factor:.4f} / {result_a.profit_factor:.4f}
                = {robustness:.4f}
                = {robustness:.2%}
```

**Status**: {'[PASS] ACCEPTABLE' if robustness >= 0.80 else '[WARN] NEEDS OPTIMIZATION' if robustness >= 0.50 else '[FAIL] SEVERE OVERFITTING'}

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
"""

with open("BASELINE_IMPULSE_REPORT.md", "w", encoding="utf-8") as f:
    f.write(report)
print("  [OK] BASELINE_IMPULSE_REPORT.md")

print("\n" + "="*80)
print("BASELINE TEST COMPLETE")
print("="*80)
