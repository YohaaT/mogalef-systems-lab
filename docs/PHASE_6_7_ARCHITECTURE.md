# Phase 6 & 7: Architecture & Validation Pipeline

## High-Level Flow

```
Phase 5 Output (top-5 combos)
         ↓
    PHASE 6: Regime-Aware Holdout Validation
    • Input: top-5 from Phase 5 + last 20% CSV (holdout)
    • Process: Backtest each combo on holdout
    • Validation: Check PF ≥ 0.8 in ALL volatility regimes
    • Output: 3-5 combinations that PASSED phase 6
         ↓
    PHASE 7: End-to-End Consistency Backtest
    • Input: Phase 6 passing combos + 100% CSV
    • Process: Single continuous backtest (no splits, no folds)
    • Validation: Check annual consistency, max DD, monthly wins
    • Output: PRODUCTION-READY strategy (1-3 combos)
         ↓
    Final Gate: Annual Profitable% ≥ 70%, Max DD < 25%
```

---

## Phase 6: Regime-Aware Holdout Validation

### Why This Phase?
After Phases 1-5 optimize on 80% of data, Phase 6 verifies profitability on the **never-touched last 20%** (holdout). Tests if the strategy overfitted or generalizes.

### Process (Diagram)

```
Phase 5 Top-5 JSON
      ↓
[Combo 1] [Combo 2] [Combo 3] [Combo 4] [Combo 5]
      ↓
For each combo:
  1. Load holdout data (last 20% of CSV)
  2. Run strategy.run(holdout_data)
  3. Calculate: PF, trades, max_dd
  4. Split holdout into 3 ATR regimes (low/med/high)
  5. Recalculate PF per regime
         ↓
      Acceptance Check:
      ✓ Phase 6 PF ≥ 0.8
      ✓ min(low_pf, med_pf, high_pf) ≥ 0.8  ← CRITICAL
      ✓ Degradation (Phase5→6) < 20%
         ↓
   PASSED? → keep for Phase 7
   FAILED? → reject (overfitted or regime-fragile)
```

### Key Metrics

| Metric | Interpretation | Threshold |
|--------|-----------------|-----------|
| Phase 6 PF | Holdout profitability | ≥ 0.8 |
| Low-Vol PF | Performs in quiet markets | ≥ 0.8 |
| Med-Vol PF | Performs in normal volatility | ≥ 0.8 |
| High-Vol PF | Performs in stressed markets | ≥ 0.8 |
| Degradation % | In-sample overfitting signal | < 20% |

### Example Output
```json
{
  "rank": 1,
  "phase5_pf": 1.45,
  "phase6_pf": 1.32,
  "degradation_pct": 9.0,  ✓ OK (< 20%)
  "regime_validation": {
    "low_vol_pf": 1.28,     ✓ OK (≥ 0.8)
    "med_vol_pf": 1.35,     ✓ OK (≥ 0.8)
    "high_vol_pf": 0.95     ✓ OK (≥ 0.8)
  },
  "passed": true
}
```

---

## Phase 7: End-to-End Consistency Backtest

### Why This Phase?
Walk-forward (Phases 1-5) tests robustness across windows, but doesn't show **continuous equity behavior**. A strategy can have good walk-forward PF but terrible drawdowns or bad years. Phase 7 catches this by running the strategy continuously from start to end of data.

### Process (Diagram)

```
Phase 6 Passing Combos
         ↓
For each combo:
  1. Load FULL CSV (100%, no train/test split)
  2. Run strategy.run(full_data) once
  3. Collect continuous equity curve
         ↓
Analyze across full history:
  
  a) Annual Breakdown (by year):
     Year 2022: 1850 trades, PF=1.25 ✓ profitable
     Year 2023: 2100 trades, PF=0.95 ✗ LOSING YEAR
     Year 2024: 2200 trades, PF=1.42 ✓ profitable
     Year 2025: 1882 trades, PF=1.18 ✓ profitable
     
  b) Monthly Breakdown:
     Count: 120 months, 75 positive, 45 negative
     Win rate: 62.5% months profitable
     
  c) Regime Breakdown (low/med/high ATR):
     Low Vol:  3000 trades, PF=1.42
     Med Vol:  3500 trades, PF=1.35
     High Vol: 1932 trades, PF=1.28
     
  d) Drawdown Analysis:
     Max DD: 18.5%
     Max DD Duration: 2156 bars (~1.5 years)
     Recovery Time: 3421 bars (~2.4 years)
         ↓
Acceptance Gate (ALL must pass):
  ✓ Annual profitable% ≥ 70% (max 30% losing years)
  ✓ Max DD < 25%
  ✓ No 6+ months consecutive collapse
  ✓ All regimes PF ≥ 0.8
  ✓ Monthly positive% ≥ 50%
  ✓ Trades per year ≥ 50 (enough volume)
         ↓
PRODUCTION-READY? → Yes/No
```

### Key Metrics

| Metric | What It Measures | Threshold |
|--------|------------------|-----------|
| Annual Profitable % | Consistency across years | ≥ 70% |
| Max Drawdown | Worst case loss | < 25% |
| Monthly Win % | Month-to-month consistency | ≥ 50% |
| Regime Stability | Works in all vol regimes | All ≥ 0.8 |
| Max Consecutive Collapse | Longest losing period | < 6 months |
| Trades/Year | Signal robustness | ≥ 50 |

### Example Output Summary

```
Strategy: ES_5m_001_rank1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Full History (4 years, 189k bars):
  • Total PF: 1.38
  • Total Trades: 8,432
  • Max Drawdown: 18.5%

Annual Breakdown:
  2022: PF=1.25 ✓ (1,850 trades)
  2023: PF=0.95 ✗ (2,100 trades) ← Losing year
  2024: PF=1.42 ✓ (2,200 trades)
  2025: PF=1.18 ✓ (1,882 trades)
  
  Annual Profitable%: 75% (3/4 years) ✓

Monthly:
  Positive Months: 75/120 (62.5%) ✓

Regime Breakdown:
  Low Vol:  PF=1.42 ✓
  Med Vol:  PF=1.35 ✓
  High Vol: PF=1.28 ✓

Final Verdict: PASSED ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ready for paper trading / live deployment
```

---

## Data Split Strategy

```
Full CSV Data (100%)
│
├─ 0% ──────────── 80% ──────────────── 100%
│  └─────────────────────────────────────┘
│                  Phases 1-5
│             (5 walk-forward windows)
│             (training + validation)
│
└─────────────────────── 80% ─────────────── 100%
                              Phase 6 HOLDOUT
                          (never touched in 1-5)
                         (out-of-sample test)

Phase 7: Uses 100% (full continuous backtest)
```

### Critical Rule
**Last 20% of CSV must NOT be touched by any Phase 1-5 fold or window.** Implement:

```python
holdout_cutoff = int(len(data) * 0.8)
data_for_phases_1to5 = data[:holdout_cutoff]      # 80%
holdout_for_phase6 = data[holdout_cutoff:]        # 20%, reserved
full_data_for_phase7 = data                        # 100%
```

---

## Implementation Timeline

| Phase | Task | Duration | Dependencies |
|-------|------|----------|--------------|
| Phase 6 | regime-aware validation | 2-4h | Phase 5 done |
| Phase 7 | end-to-end consistency | 8-12h | Phase 6 done |
| **Total** | **Both phases** | **10-16h** | **Phase 5 first** |

---

## Success Criteria

### Minimum for "Good" Strategy
- ✅ Passes Phase 6: PF_holdout ≥ 0.8, all regimes ≥ 0.8
- ✅ Passes Phase 7: ≥70% annual profitable, max DD < 25%

### Minimum for "Production Ready"
- ✅ Passes all Phase 7 gates
- ✅ No regime fragility (works equally in all volatility)
- ✅ Max drawdown < 20% (safer than 25% threshold)
- ✅ Positive months ≥ 60% (high consistency)

---

## Files Generated

### Phase 6 Outputs
- `phase6_holdout_{ASSET}_{TF}_{COMB}_top5_validation.json` (per pipeline)
- Summary: `phase6_validation_SUMMARY.csv`

### Phase 7 Outputs
- `phase7_consistency_{ASSET}_{TF}_{COMB}_summary.json` (per combo, ranked)
- `phase7_consistency_FULL_REPORT.csv` (all combos, 1 row each)
- `phase7_equity_curves/{ASSET}_{TF}_{COMB}_rank{N}_equity.html` (interactive charts)

### Final Report
- `FINAL_PRODUCTION_READY_STRATEGIES.csv` (only combos that passed all gates)
- `FINAL_EQUITY_CURVES/` (best 3-5 strategies with detailed visualizations)

---

## Quick Reference: Acceptance Gates

```
┌─────────────────────────────────────────────────────┐
│ PHASE 6 ACCEPTANCE GATE                             │
├─────────────────────────────────────────────────────┤
│ ✓ Phase 6 PF ≥ 0.8                                 │
│ ✓ min(low_pf, med_pf, high_pf) ≥ 0.8              │
│ ✓ Degradation (Phase5→6) < 20%                    │
│ ✓ Holdout trades ≥ 15                              │
└─────────────────────────────────────────────────────┘
         ↓ PASSED?
         
┌─────────────────────────────────────────────────────┐
│ PHASE 7 ACCEPTANCE GATE                             │
├─────────────────────────────────────────────────────┤
│ ✓ Annual profitable% ≥ 70%                          │
│ ✓ Max Drawdown < 25%                               │
│ ✓ No 6+ months consecutive collapse                │
│ ✓ All regimes PF ≥ 0.8                             │
│ ✓ Monthly positive% ≥ 50%                          │
│ ✓ Trades per year ≥ 50                             │
└─────────────────────────────────────────────────────┘
         ↓ PASSED?
         
    PRODUCTION READY ✓
```

