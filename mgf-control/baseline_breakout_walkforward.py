"""Baseline Walk-Forward Backtest for COMB_003 Breakout Trading (Version C)

Test default parameters on Phase A (training) and Phase B (unseen validation)
to establish robustness baseline before optimization.
"""

import csv
import json
from pathlib import Path
from COMB_003_BREAKOUT_V1 import Comb003BreakoutStrategy, Comb003BreakoutParams, load_ohlc_csv

print("="*80)
print("COMB_003 BREAKOUT TRADING - BASELINE WALK-FORWARD TEST")
print("="*80)

# Load Phase A and Phase B
print("\n[1] Loading data...")
phase_a_rows = load_ohlc_csv("YM_phase_A_clean.csv")
phase_b_rows = load_ohlc_csv("YM_phase_B_clean.csv")
print(f"Phase A: {len(phase_a_rows)} rows")
print(f"Phase B: {len(phase_b_rows)} rows")

# Test default parameters
print("\n[2] Testing default parameters...")
params = Comb003BreakoutParams()
strategy = Comb003BreakoutStrategy(params)

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
    print(f"[WARN] Robustness < 80% (got {robustness:.2%})")

# Export results
print("\n[4] Exporting results...")

# Phase A trades
strategy.export_trades_csv(result_a.trades, "baseline_breakout_phase_a_trades.csv")
print("  [OK] baseline_breakout_phase_a_trades.csv")

# Phase B trades
strategy.export_trades_csv(result_b.trades, "baseline_breakout_phase_b_trades.csv")
print("  [OK] baseline_breakout_phase_b_trades.csv")

# Phase A summary
strategy.export_summary_json(result_a, "baseline_breakout_phase_a_summary.json")
print("  [OK] baseline_breakout_phase_a_summary.json")

# Phase B summary
strategy.export_summary_json(result_b, "baseline_breakout_phase_b_summary.json")
print("  [OK] baseline_breakout_phase_b_summary.json")

# Generate report
report = f"""# COMB_003 Breakout Trading - Baseline Walk-Forward Report

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
"""

with open("BASELINE_BREAKOUT_REPORT.md", "w", encoding="utf-8") as f:
    f.write(report)
print("  [OK] BASELINE_BREAKOUT_REPORT.md")

print("\n" + "="*80)
print("BASELINE TEST COMPLETE")
print("="*80)
