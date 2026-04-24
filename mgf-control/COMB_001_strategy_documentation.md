# COMB_001 Strategy Documentation

## 1. Executive summary

`COMB_001` is the main strategy branch currently defined for disciplined exploration inside `mogalef-systems-lab`.

Its design goal is simple and explicit:
- use `EL_STPMT_DIV` as the entry engine,
- use `EL_Mogalef_Trend_Filter_V2` as the regime permission layer,
- use a simple causal stop as the initial risk and exit layer,
- preserve a clean temporal contract for reproducible testing.

This strategy is intentionally minimal. It is meant to be traceable, comparable, and reusable as a clean base branch.
It is **not** documented as a final validated production strategy.

---

## 2. Strategy identity

**Strategy name:** `COMB_001`  
**Project:** `mogalef-systems-lab`  
**Role in project:** main exploratory branch  
**Current methodological status:** reusable exploratory strategy for provisional ranking and controlled iteration

---

## 3. Components used

### 3.1 Entry engine
**Component:** `EL_STPMT_DIV`

Purpose:
- detect actionable long or short directional signals.

Operational interpretation used in `COMB_001`:
- long setup when `pose == 1`
- short setup when `pose == -1`

### 3.2 Regime filter
**Component:** `EL_Mogalef_Trend_Filter_V2`

Purpose:
- allow or block entries depending on market regime context.

Operational interpretation used in `COMB_001`:
- trading is allowed only when `sentiment == "pass"`

### 3.3 Risk and exit layer
**Component:** simple causal stop

Purpose:
- keep the branch executable without introducing known non-causal contamination from more complex retrospective components.

Operational interpretation used in `COMB_001`:
- long initial stop = low of the signal bar
- short initial stop = high of the signal bar
- exit also allowed on valid opposite signal
- exit at end of available dataset if still open

---

## 4. What the strategy does

In plain terms, `COMB_001` does this:

1. observe a closed bar `t`
2. compute the STPMT directional signal on that bar
3. compute the Trend Filter permission state on that bar
4. if both align and no position is open, prepare an entry
5. execute the entry at the open of bar `t+1`
6. manage the open trade causally with a simple initial stop and possible opposite-signal exit

This keeps the branch methodologically cleaner than previous contaminated runs that depended on retrospective structure or non-causal stop behavior.

---

## 5. Exact trading rules

## 5.1 Long entry rule
Open a long position only if, on closed bar `t`:
1. `EL_STPMT_DIV` emits long signal, `pose == 1`
2. `EL_Mogalef_Trend_Filter_V2` allows trading, `sentiment == "pass"`
3. there is no existing open position

Execution:
- enter on the open of bar `t+1`

## 5.2 Short entry rule
Open a short position only if, on closed bar `t`:
1. `EL_STPMT_DIV` emits short signal, `pose == -1`
2. `EL_Mogalef_Trend_Filter_V2` allows trading, `sentiment == "pass"`
3. there is no existing open position

Execution:
- enter on the open of bar `t+1`

## 5.3 Initial stop rule
### Long trade
- initial stop = low of the signal bar

### Short trade
- initial stop = high of the signal bar

## 5.4 Exit rule
Exit the current position if any of the following happens:
1. the stop is touched
2. a valid opposite signal appears and the filter still allows trading
3. the dataset ends while the position remains open

## 5.5 Position management constraints
- one position at a time
- no pyramiding
- no fixed target in the current base version
- no complex trailing logic in the current base version
- no advanced money management in the current base version

---

## 6. Temporal methodology

The temporal contract of `COMB_001` is part of the strategy definition and must not be changed silently.

### Required sequence
1. evaluate setup on closed bar `t`
2. decide whether setup is valid on that same bar
3. execute entry on open of `t+1`
4. manage position only with information available from the trade life onward

### Why this matters
This rule exists to reduce temporal contamination and keep results interpretable.
If execution is moved back onto the signal bar itself, the strategy definition changes and results are no longer comparable with the documented branch.

---

## 7. Data contract

The Python implementation expects a canonical OHLC CSV with at least these columns:
- `timestamp_utc`
- `open`
- `high`
- `low`
- `close`

Optional fields such as `volume` or `symbol` may exist, but are not required by the base implementation.

---

## 8. Output behavior of the Python implementation

The implementation in `mgf-control/COMB_001.py` produces:
- trade list with timestamps and prices
- side of trade
- stop used
- exit reason
- bars in trade
- per-trade points result
- aggregate equity in points
- win/loss counts

This makes the base branch suitable for reproducible inspection and controlled iteration.

---

## 9. Explicit exclusions

`COMB_001` in its base documented form does **not** include:
- `EL_MOGALEF_Bands`
- `EL_Stop_Intelligent`
- fixed target logic
- advanced sizing
- portfolio-level overlays
- multi-position logic

Those exclusions are deliberate and help preserve the branch as a clean research baseline.

---

## 10. Professional interpretation

`COMB_001` should be understood as a disciplined research strategy template, not as a final production-ready trading system.

Its value is:
- clean logic,
- explicit execution timing,
- reusable component boundaries,
- straightforward auditability,
- comparability against future controlled variants.

Its current limitations are also explicit:
- limited historical validation,
- exploratory status,
- no claim of robust edge,
- simplified exit architecture.

---

## 11. Files delivered for COMB_001

- `mgf-control/COMB_001.py`
- `mgf-control/COMB_001_params.txt`
- `mgf-control/COMB_001_strategy_documentation.md`

---

## 12. Recommended next professional step

Use this documented base as the only authoritative implementation of `COMB_001`, then build future variants as explicit children of this branch rather than modifying the branch definition silently.
