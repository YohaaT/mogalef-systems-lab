# COMB_001 Trend Trading (Version A) - Strategy Specification

## 1. Executive Summary

**COMB_001 Trend Trading Version A** is a disciplined, reproducible trend trading system designed following Eric Mogalef's automated trading methodology from *Trading automatique - conception et sécurisation*.

**Purpose**: Serve as the authoritative implementation of Mogalef-compliant Trend Trading for the mogalef-systems-lab project.

**Key Design Goals**:
- Independent optimization of 4 components (Signal → Contexto → Exits → Stops)
- Strict causal execution (no lookahead)
- Professional robustness validation via walk-forward testing
- Clean component boundaries enabling isolated testing

**Status**: Exploratory baseline for controlled iteration. NOT a production-ready system; suitable for research and further refinement.

---

## 2. Strategy Identity

| Property | Value |
|----------|-------|
| **Strategy Name** | COMB_001_TREND |
| **Version** | 1.0 |
| **Type** | Trend Trading (per Mogalef classification) |
| **Project** | mogalef-systems-lab |
| **Role** | Main exploratory branch with professional validation framework |
| **Methodology** | Independent component optimization (Mogalef framework) |
| **Status** | Reusable research baseline |

---

## 3. Components Used

### 3.1 Signal (Entry Detection)

**Component**: `EL_STPMT_DIV` (4-Stochastic Divergence Detector)

**Function**: Identify actionable directional setups via oscillator divergence.

**How It Works**:
- Composites 4 stochastic oscillators (periods: 5, 14, 45, 75)
- Smooths each with SMA (lengths: 3, 3, 14, 20)
- Weights and averages: (4.1×d1 + 2.5×d2 + d3 + 4.0×d4) / 11.6
- Detects divergences:
  - **Bullish**: Indicator makes lower low, price makes higher low → **pose = 1**
  - **Bearish**: Indicator makes higher high, price makes lower high → **pose = -1**

**Operational Interpretation in COMB_001**:
- `pose == 1` → Long setup candidate
- `pose == -1` → Short setup candidate
- `pose == None` → No setup

**Parameters** (configurable):
- `smooth_h`: Smoothing for HIGH extremes (default 2, optimize in Phase 1)
- `smooth_b`: Smoothing for LOW extremes (default 2, optimize in Phase 1)
- `distance_max_h/l`: Lookback for pivot detection (default 200, optimize in Phase 1)

---

### 3.2 Contexto (Regime Permission Layer)

**Three Independent Filters**:

#### 3.2.1 Trend Filter
**Component**: `EL_Mogalef_Trend_Filter_V2` (3-Repulse Trend Regime Indicator)

**Function**: Block or allow entry based on multi-timeframe trend alignment.

**How It Works**:
- Computes 3 repulsion indicators at different scales (r1=1, r2=90, r3=150)
- Each repulsion measures "push up" vs "push down" forces
- Maps to 8 trend cases based on (r1_dir, r2_dir, r3_dir) combination
- Outputs `sentiment`:
  - `"pass"` → Current regime is tradeable
  - `"block"` → Regime is NOT tradeable (filter says no)

**Operational Interpretation in COMB_001**:
- Entry allowed ONLY if `sentiment == "pass"`
- `trend_trade_only_case = 0` (AllPass mode): Trade all cases except explicitly blocked
- `trend_off_on = 1` (Active): Respect filter verdicts

**Parameters** (configurable):
- `trend_r2`: Intermediate trend window (default 90, optimize in Phase 2)
- `trend_r3`: Long-term trend window (default 150, optimize in Phase 2)

---

#### 3.2.2 Horaire Filter (Time-of-Day)
**Function**: Block trades outside designated UTC hours.

**Operational Interpretation in COMB_001**:
- Entry allowed ONLY if `hour(timestamp) in [9, 10, 11, 12, 13, 14, 15]` (UTC)
- Blocks early Asian session (low volatility, whipsaw risk)
- Blocks late NY session (after-hours, reduced liquidity)

**Parameters** (configurable):
- `horaire_allowed_hours_utc`: List of allowed hours (default [9-15], optimize in Phase 2)

---

#### 3.2.3 Volatility Filter (ATR Range)
**Function**: Block trades if volatility is outside expected range.

**Operational Interpretation in COMB_001**:
- Entry allowed ONLY if `volatility_atr_min <= ATR[signal_bar] <= volatility_atr_max`
- Very low ATR: Whipsaw risk, insufficient trend strength
- Very high ATR: Uncontrollable slippage, gap risk

**Parameters** (configurable):
- `volatility_atr_min`: Minimum acceptable ATR (default 0.0, optimize in Phase 2)
- `volatility_atr_max`: Maximum acceptable ATR (default 500.0, optimize in Phase 2)
- `volatility_atr_period`: ATR calculation period (fixed 14, not optimized)

---

### 3.3 Exits (Position Management)

**Four Exit Conditions** (in priority order):

#### 3.3.1 Stop Loss
**Trigger**: Position touches or crosses stop price.

**Stop Price Determination**:
- Primary: Use `Stop Inteligente` (volatility-adaptive trailing stop)
- Fallback: Use signal bar extreme (low for long, high for short)

**Exit Execution**: Exit immediately when price touches stop.

**Exit Reason Code**: `"stop"`

**Rationale**: Loss limitation (essential risk control).

---

#### 3.3.2 Profit Target
**Trigger**: Position reaches dynamic 10 ATR objective.

**Target Price Calculation**:
```
LONG:  target = entry_price + (10 × ATR[signal_bar])
SHORT: target = entry_price - (10 × ATR[signal_bar])
```

**Exit Execution**: Exit when high (long) or low (short) touches target.

**Exit Reason Code**: `"target"`

**Rationale**: Discipline-based profit taking; 10 ATR per Mogalef DOW Jones research showing optimal risk/reward.

---

#### 3.3.3 Opposite Signal
**Trigger**: Reverse divergence detected AND Trend Filter still allows.

**Condition**:
```
LONG position:  exit if (pose[bar_i] == -1) AND (sentiment[bar_i] == "pass")
SHORT position: exit if (pose[bar_i] == 1) AND (sentiment[bar_i] == "pass")
```

**Exit Execution**: Exit on bar i+1 open (causal).

**Exit Reason Code**: `"opposite_signal"`

**Rationale**: Signal-based reversal (market structure confirmation).

---

#### 3.3.4 TimeStop (Duration Limit)
**Trigger**: Position exceeds 30 bars duration.

**Condition**:
```
if bars_in_trade >= 30:
    exit on close of bar
```

**Exit Reason Code**: `"timescan"`

**Rationale**: Trend Trading discipline (per Mogalef: 30 bars max for trend trades).

---

### 3.4 Risk and Stops

**Component**: `Stop Inteligente` (Volatility-Adaptive Trailing Stop)

**Function**: Intelligent trailing stop that adapts spacing to recent volatility.

**How It Works**:
- Calculates recent volatility (2-bar TR SMA)
- Calculates reference volatility (20-bar TR SMA)
- Computes dynamic spacing: `space = ((2 × ref_vol) - recent_vol) × coef_volat / 5`
- Places stop at: local_extreme ± spacing
- Ratchets stop higher (long) / lower (short) as price moves favorably
- Never lets stop move below (long) / above (short) previous bar's stop

**Operational Interpretation in COMB_001**:
- Used at entry bar (`i+1`) to set initial stop
- Allows stop to trail upward (long) or downward (short) during position life
- Reduces average loss vs fixed stops

**Parameters** (configurable in Phase 4):
- `quality`: Extremum detection sensitivity (default 2)
- `recent_volat`: Recent volatility window (default 2)
- `ref_volat`: Reference volatility window (default 20)
- `coef_volat`: Volatility scaling (default 5.0)

**Fallback**: If Stop Inteligente unavailable, use signal bar low/high:
```
LONG:  stop = low[signal_bar]
SHORT: stop = high[signal_bar]
```

---

## 4. What the Strategy Does (Plain Language)

1. **Observe a closed bar `t`** (signal bar).
2. **Compute components**:
   - STPMT divergence signal → `pose` (1 for long, -1 for short, None for no signal)
   - Trend Filter regime → `sentiment` ("pass" or "block")
   - Current hour, current ATR
3. **Check entry conditions**:
   - `pose != None` (signal exists)
   - `sentiment == "pass"` (filter allows)
   - `current_hour in [9-15]` (time filter)
   - `volatility_atr_min <= ATR <= volatility_atr_max` (volatility filter)
   - No position currently open
4. **If all conditions met**: Mark entry for bar `t+1` open
5. **Execute entry** at open of bar `t+1`
6. **Set initial stop** using Stop Inteligente (or fallback signal bar extreme)
7. **Set profit target** at entry ± 10 × ATR
8. **Manage position**:
   - Check 4 exit conditions each bar (in priority order)
   - Exit on first trigger
   - Log exit reason and trade P&L

---

## 5. Exact Trading Rules

### 5.1 Long Entry Rule

**Precondition**: On closed bar `t`, ALL of the following must be true:
1. `EL_STPMT_DIV.pose[t] == 1` (bullish divergence)
2. `EL_Mogalef_Trend_Filter_V2.sentiment[t] == "pass"` (filter allows)
3. `hour(timestamp[t]) in [9, 10, 11, 12, 13, 14, 15]` (UTC hour allowed)
4. `volatility_atr_min <= ATR[t] <= volatility_atr_max` (volatility in range)
5. No existing open position

**Execution**:
- Enter on the **open of bar `t+1`**
- Entry price = `open[t+1]`
- Entry side = "long"

---

### 5.2 Short Entry Rule

**Precondition**: On closed bar `t`, ALL of the following must be true:
1. `EL_STPMT_DIV.pose[t] == -1` (bearish divergence)
2. `EL_Mogalef_Trend_Filter_V2.sentiment[t] == "pass"` (filter allows)
3. `hour(timestamp[t]) in [9, 10, 11, 12, 13, 14, 15]` (UTC hour allowed)
4. `volatility_atr_min <= ATR[t] <= volatility_atr_max` (volatility in range)
5. No existing open position

**Execution**:
- Enter on the **open of bar `t+1`**
- Entry price = `open[t+1]`
- Entry side = "short"

---

### 5.3 Initial Stop Rule

**For Long Trade**:
- Primary: `stop = Stop_Inteligente[t+1]` (if available)
- Fallback: `stop = low[t]` (signal bar low)

**For Short Trade**:
- Primary: `stop = Stop_Inteligente[t+1]` (if available)
- Fallback: `stop = high[t]` (signal bar high)

---

### 5.4 Exit Rules (Priority Order)

**Condition 1 - Stop Loss Hit**:
- LONG: `if low[i] <= stop_price`
- SHORT: `if high[i] >= stop_price`
- Exit reason: `"stop"`

**Condition 2 - Target Reached**:
- LONG: `if high[i] >= entry_price + (10 × ATR[t])`
- SHORT: `if low[i] <= entry_price - (10 × ATR[t])`
- Exit reason: `"target"`

**Condition 3 - Opposite Signal**:
- LONG: `if pose[i] == -1 AND sentiment[i] == "pass"`
- SHORT: `if pose[i] == 1 AND sentiment[i] == "pass"`
- Exit on bar i+1 open (causal)
- Exit reason: `"opposite_signal"`

**Condition 4 - TimeStop**:
- `if bars_in_trade >= 30`
- Exit on close of bar
- Exit reason: `"timescan"`

**Condition 5 - End of Dataset**:
- If bar is last bar and position still open
- Exit on close (or next available price)
- Exit reason: `"end_of_data"` (exclude from analysis)

---

### 5.5 Position Management Constraints

- **One position at a time**: No pyramiding, no scaling
- **One-sided exposure**: Long OR short, never both
- **No fixed target in stop loss**: Stop and target are independent levels
- **No complex trailing logic**: Stop Inteligente handles adaptation
- **No advanced money management**: Fixed 1 contract per trade

---

## 6. Temporal Methodology

**The temporal contract is part of the strategy definition and must NOT be changed silently.**

### Required Sequence

```
Bar t (closed): 
  1. Evaluate setup on this CLOSED bar
  2. Decide whether setup is valid on this same bar
  3. Mark entry_index = t+1

Bar t+1 (next bar):
  1. Execute entry at OPEN of bar t+1
  2. Calculate stop, target, position size
  
Bars t+2, t+3, ...:
  1. Manage position with information available from this bar onward
  2. Check exit conditions
  3. Close if exit triggered
```

### Why This Matters

This temporal rule exists to:
1. **Reduce lookahead bias**: Use only information known on bar `t`
2. **Match real-world execution**: Signal appears → entry next day open
3. **Enable reproducibility**: Results are comparable with documented branch definition
4. **Prevent silent redefinition**: If execution is moved to signal bar itself, strategy definition changes

---

## 7. Data Contract

### Required Columns

The Python/NT8 implementation expects a canonical OHLC CSV with:
- `timestamp_utc` (format: YYYY-MM-DD HH:MM:SS)
- `open` (float)
- `high` (float)
- `low` (float)
- `close` (float)

### Optional Columns

May exist in CSV but are not required:
- `volume`
- `symbol`
- `date` (alternative timestamp format)

### Minimum Data Length

- **Global minimum**: 150 bars (for Trend Filter warmup with r3=150)
- **Recommended minimum**: 500 bars per test period (sufficient for stable statistics)

---

## 8. Output Behavior

The Python implementation (`COMB_001_TREND_V1.py`) produces:

### Per-Trade Output

For each completed trade:
- Entry/exit timestamps and prices
- Side (long/short)
- Stop used and target set
- Exit reason (stop, target, opposite_signal, timescan)
- Bars in trade
- Per-trade P&L in points
- ATR at entry

### Aggregate Output

- Total equity points
- Trade count
- Win count / Loss count
- Win rate (%)
- Profit Factor
- Max drawdown
- Average win / Average loss
- Exit reason distribution

This output format makes the base branch suitable for:
- Reproducible inspection
- Controlled iteration
- Walk-forward validation
- Component optimization

---

## 9. Explicit Exclusions

**COMB_001 Trend Trading in its base documented form does NOT include**:

- ❌ `EL_MOGALEF_Bands` (Mogalef Bands; reserved for future structural analysis)
- ❌ Dynamic `target_atr_multiplier` (fixed at 10.0; only vary if Phase 3 justifies)
- ❌ `EL_Stop_Intelligent` enhancements beyond Phase 4 optimization
- ❌ Fixed target logic (must remain dynamic, ATR-based)
- ❌ Advanced sizing or leverage
- ❌ Portfolio-level overlays or correlation filters
- ❌ Multi-position logic or spread trading
- ❌ Options or derivatives
- ❌ Intrabar (tick-level) execution

These exclusions are **deliberate** and preserve COMB_001 as a clean research baseline.

---

## 10. Professional Interpretation

**COMB_001 Trend Trading should be understood as**:

### Value Proposition
- ✓ Clean, explicit logic
- ✓ Reproducible execution timing
- ✓ Reusable component boundaries
- ✓ Straightforward auditability
- ✓ Professional walk-forward validation framework
- ✓ Compliant with Mogalef methodology

### Current Limitations (Explicit)
- ⚠ Limited historical validation (exploratory)
- ⚠ Research/exploratory status, not production
- ⚠ No claim of robust competitive edge
- ⚠ Simplified risk architecture (no portfolio risk mgmt)
- ⚠ Not advisable for live trading without extensive validation

### Use Cases
- **Suitable for**:
  - Research and methodology validation
  - Performance baseline for variants
  - Teaching Mogalef concepts
  - Controlled parameter optimization
- **Not suitable for**:
  - Live trading without additional validation
  - Capital allocation decisions without reserve capital
  - Claims of statistical edge without proper testing

---

## 11. Files Delivered for COMB_001 Trend Trading Version A

### Documentation Files

- `COMB_001_TREND_strategy_spec.md` (this file) — Formal specification
- `COMB_001_TREND_V1_params.txt` — Parameter ranges and optimization guide
- `COMB_001_TREND_backtest_protocol.md` — Walk-forward testing methodology
- `COMB_001_TREND_historical_baseline_documentation.md` — Validation against known results (if applicable)

### Implementation Files

- `COMB_001_TREND_V1.py` — Python backtest engine (canonical implementation)
- `COMB001_TREND.cs` — NinjaScript C# port for NT8 (execution reference)

### Results Files (Generated During Backtest)

- `COMB_001_TREND_trades_phase_A.csv` — Trade log for Phase A (training)
- `COMB_001_TREND_trades_phase_B.csv` — Trade log for Phase B (validation)
- `COMB_001_TREND_summary_phase_A.json` — Metrics for Phase A
- `COMB_001_TREND_summary_phase_B.json` — Metrics for Phase B
- `Phase1_OptimizationLog.txt` — Signal component optimization iterations
- `Phase2_OptimizationLog.txt` — Contexto component optimization iterations
- `Phase3_OptimizationLog.txt` — Exits component optimization iterations
- `Phase4_OptimizationLog.txt` — Stops component optimization iterations
- `COMB_001_TREND_FinalValidationReport.md` — Combined results and capital planning

---

## 12. Recommended Next Professional Step

**Use this documented base as the ONLY authoritative implementation** of COMB_001 Trend Trading Version A.

**Future variants** should be:
1. Explicitly named (e.g., `COMB_001_TREND_V2_Bands`, `COMB_001_TREND_V2_Impulse`)
2. Documented as separate branches (not silent modifications)
3. Justified against this baseline with walk-forward validation
4. Tested in isolation on Phase B data before claiming improvement

**Methodological rigor**: Each variant exists as a controlled experiment, not an ad-hoc tweak. This enables genuine learning and prevents optimization chasing.

---

## Appendix: Mogalef Methodology Reference

This strategy implements the core concepts from Eric Mogalef's *Trading automatique - conception et sécurisation*:

| Concept | Implementation |
|---------|-----------------|
| Independent component optimization | Phases 1-4 lock prior results |
| Trend Trading specification | 30-bar TimeStop, 10 ATR target |
| Trend Filter (multi-timeframe regime) | EL_Mogalef_Trend_Filter_V2 |
| Divergence signal | EL_STPMT_DIV |
| Volatility-adaptive stop | Stop Inteligente |
| Multiple systems for safety | Recommendation for Phase 5 |
| Walk-forward validation | Phase A training, Phase B validation |
| Capital requirement (Max DD × 10) | Calculated post-backtest |

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-20  
**Status**: Approved for implementation
