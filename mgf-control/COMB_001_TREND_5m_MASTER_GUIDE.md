# COMB_001_TREND (5m) — Master Execution Guide

## Overview

Complete Phase 1-4 optimization for COMB_001_TREND strategy on YM 5-minute timeframe, following Eric Mogalef's independent optimization methodology from "Trading Automatique: Conception et Sécurisation".

**Timeline**: ~2.5-3 hours total
- Phase 1: 30-40 min (in parallel on TANK + VPS)
- Phase 2: 20-25 min (sequential sub-phases)
- Phase 3: 10-15 min
- Phase 4: 20-30 min (can be parallel on 2 servers)

---

## Phase 1: Signal Optimization (625 combos)

**Status**: ✅ **RUNNING NOW** — TANK Block 1 (175) + VPS Block 2 (450)

```bash
# Already launched:
ssh tank "cd ~/phase2_work && python3 phase1_5m_signal_block_runner.py 1" 
ssh bo "cd ~/phase2_parallel && python3 phase1_5m_signal_block_runner.py 2"

# When complete, consolidate:
python phase1_5m_consolidate.py
# Output: phase1_5m_best_params.json
```

**Optimizes**: smooth_h, smooth_b, distance_max_h/l (STPMT signal)  
**Locks**: Contexto defaults, exits, stops  
**Time**: ~35-40 min

---

## Phase 2: Contexto Filters (4 sub-phases)

**Sequential execution**: Each loads Phase 1 best + locks it

### 2a — Trend Filter (150 combos)
```bash
python phase2a_5m_trend_filter_optimizer.py
# Output: phase2a_5m_trend_filter_best_params.json
# Time: ~15 min
```
**Optimizes**: r1, r2, r3 (Mogalef Trend Filter)

### 2b — Horaire Profiles (6 tests)
```bash
python phase2b_5m_horaire_optimizer.py
# Output: phase2b_5m_horaire_best_params.json
# Time: ~3 min
```
**Optimizes**: UTC hour ranges (9-16, 9-16+20-22, etc.)

### 2c — Volatility Profiles (5 tests)
```bash
python phase2c_5m_volatility_optimizer.py
# Output: phase2c_5m_volatility_best_params.json
# Time: ~2 min
```
**Optimizes**: ATR bands (min/max)

### 2d — Weekday Filter (4 combos)
```bash
python phase2d_5m_weekday_filter_optimizer.py
# Output: phase2d_5m_weekday_best_params.json
# Time: ~1 min
```
**Optimizes**: blocked weekdays (no Monday/Tuesday)

### 2 Consolidate
```bash
python phase2_5m_consolidate.py
# Output: phase2_5m_best_params.json (final Phase 2 params)
# Time: <1 min
```

**Total Phase 2**: ~20-25 min (sequential)

---

## Phase 3: Exits Optimization (16 combos)

```bash
python phase3_5m_exits_optimizer.py
# Output: phase3_5m_exits_best_params.json
# Time: ~10-15 min
```

**Optimizes**: target_atr_multiplier [7.0, 8.0, 9.0, 10.0] × timescan_bars [20, 25, 30, 35]  
**Locks**: Phase 1 signal + Phase 2 contexto  
**Time**: ~10-15 min

---

## Phase 4: Stops Optimization (108 combos)

### Single server:
```bash
python phase4_5m_stops_optimizer.py
# Output: phase4_5m_stops_best_params.json
# Time: ~25-30 min
```

### OR parallel across 2 servers (faster):
```bash
# TANK (Block 1, 48 combos):
ssh tank "cd ~/phase2_work && python3 phase4_5m_stops_optimizer.py 1"

# VPS (Block 2, 60 combos):
ssh bo "cd ~/phase2_parallel && python3 phase4_5m_stops_optimizer.py 2"

# Consolidate when both done:
python phase4_5m_consolidate.py
# Output: phase4_5m_best_params.json
# Time: ~15-20 min parallel (vs ~30 min serial)
```

**Optimizes**: quality, recent_volat, ref_volat, coef_volat (Stop Intelligent)  
**Locks**: Phase 1-3 all best params  
**Time**: ~20-30 min (15-20 if parallel)

---

## Final Consolidation

After Phase 4 completes:

```bash
python phase_all_consolidate.py
# Output: COMB_001_TREND_5m_FINAL_PARAMS.json
```

This merges all 4 phases into single JSON with:
- Best signal params
- Best contexto params (trend, horaire, volatility, weekday)
- Best exit params
- Best stop params
- Walk-forward metrics (Phase A PF, Phase B PF, Robustness)

---

## Files Prepared

| Phase | Scripts | Outputs |
|---|---|---|
| **1** | `phase1_5m_signal_block_runner.py` | `phase1_5m_best_params.json` |
| **2a** | `phase2a_5m_trend_filter_optimizer.py` | `phase2a_5m_trend_filter_best_params.json` |
| **2b** | `phase2b_5m_horaire_optimizer.py` | `phase2b_5m_horaire_best_params.json` |
| **2c** | `phase2c_5m_volatility_optimizer.py` | `phase2c_5m_volatility_best_params.json` |
| **2d** | `phase2d_5m_weekday_filter_optimizer.py` | `phase2d_5m_weekday_best_params.json` |
| **2 consol** | `phase2_5m_consolidate.py` | `phase2_5m_best_params.json` |
| **3** | `phase3_5m_exits_optimizer.py` | `phase3_5m_exits_best_params.json` |
| **4** | `phase4_5m_stops_optimizer.py` | `phase4_5m_stops_best_params.json` |
| **4 consol** | `phase4_5m_consolidate.py` | `phase4_5m_best_params.json` |

---

## Data Requirements

- `YM_phase_A_5m.csv` — Phase A training data (81,438 bars)
- `YM_phase_B_5m.csv` — Phase B validation data (54,544 bars)
- `COMB_001_TREND_V1_vectorized.py` — Updated with `contexto_blocked_weekdays` support

---

## Mogalef Alignment ✓

- ✅ **Signal**: STPMT divergence (Phase 1)
- ✅ **Trend Filter**: R1/R2/R3 (Phase 2a)
- ✅ **Horaire**: 9-17 + 20-22 CET tested (Phase 2b profiles)
- ✅ **Volatility**: ATR bands (Phase 2c)
- ✅ **Weekday**: No Monday/Tuesday (Phase 2d, per PDF)
- ✅ **Exits**: 10 ATR target + 30-bar TimeStop (Phase 3)
- ✅ **Stops**: Stop Intelligent trailing (Phase 4)
- ✅ **Independent**: Each phase locks previous (no cumulative optimization)
- ✅ **Walk-forward**: Phase A train / Phase B validate → robustness metric

---

## Next Steps After Phase 4

1. **Final Parameters**: Run consolidation to merge all 4 phases → `COMB_001_TREND_5m_FINAL_PARAMS.json`
2. **NT8 Port**: Update `COMB001_TREND.cs` with final optimized parameters
3. **Live Backtest**: Use NT8 Strategy Analyzer on extended historical data (Phase B + forward)
4. **COMB_002 + COMB_003**: Repeat same protocol (4 phases each)

---

## Reference

- **PDF**: `C:\Users\Yohanny Tambo\Desktop\Mogalef\Trading automatique - conception et sécurisation.pdf`
- **PDF Notes**: `MOGALEF_PDF_NOTES.md` (summary extracted, no need to re-read PDF)
- **Execution**: `PHASE2_5m_EXECUTION_GUIDE.md` (Phase 2 details)

---

**Status**: Phase 1 in progress (TANK + VPS running)  
**Prepared**: Phase 2, 3, 4 scripts ready to run sequentially  
**Est. Completion**: ~2.5-3 hours from now
