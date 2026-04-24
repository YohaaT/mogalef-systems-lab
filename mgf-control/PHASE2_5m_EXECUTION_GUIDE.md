# PHASE 2 (5m) EXECUTION GUIDE

## Prerequisites

- Phase 1 complete: `phase1_5m_best_params.json` in current directory
- 5m data ready: `YM_phase_A_5m.csv`, `YM_phase_B_5m.csv`
- Vectorized engine updated: `COMB_001_TREND_V1_vectorized.py` with `contexto_blocked_weekdays` support

## Execution Sequence (Sequential)

### Phase 2a — Trend Filter (150 combos)
```bash
python phase2a_5m_trend_filter_optimizer.py
# Output: phase2a_5m_trend_filter_best_params.json
# Time: ~15 min (multiprocessing 8 cores)
```

### Phase 2b — Horaire Profiles (6 tests)
```bash
python phase2b_5m_horaire_optimizer.py
# Output: phase2b_5m_horaire_best_params.json
# Time: ~3 min (sequential, 6 tests)
```

### Phase 2c — Volatility Profiles (5 tests)
```bash
python phase2c_5m_volatility_optimizer.py
# Output: phase2c_5m_volatility_best_params.json
# Time: ~2 min (sequential, 5 tests)
```

### Phase 2d — Weekday Filter (4 combos)
```bash
python phase2d_5m_weekday_filter_optimizer.py
# Output: phase2d_5m_weekday_best_params.json
# Time: ~1 min (sequential, 4 tests)
```

### Consolidate Phase 2
```bash
python phase2_5m_consolidate.py
# Output: phase2_5m_best_params.json (final consolidated params)
```

## Total Phase 2 Time
- **Sequential all sub-phases**: ~20-25 min
- Can run **2a on TANK/VPS in parallel** if desired (same 150 combo grid)
- 2b, 2c, 2d must run **sequentially** (each depends on previous best)

## Output Files

| File | Purpose |
|---|---|
| `phase2a_5m_trend_filter_best_params.json` | Best R1/R2/R3 values |
| `phase2a_5m_trend_filter_log.csv` | All 150 combos ranked |
| `phase2b_5m_horaire_best_params.json` | Best horaire profile |
| `phase2b_5m_horaire_log.csv` | All 6 profiles tested |
| `phase2c_5m_volatility_best_params.json` | Best volatility band |
| `phase2c_5m_volatility_log.csv` | All 5 profiles tested |
| `phase2d_5m_weekday_best_params.json` | Best weekday blocking |
| `phase2d_5m_weekday_log.csv` | All 4 combos tested |
| `phase2_5m_best_params.json` | **FINAL** Phase 2 consolidated params |

## Mogalef Alignment

✓ Signal: smooth_h/smooth_b/distance_max (Phase 1)
✓ Trend Filter: R1/R2/R3 (Phase 2a, optional per Mogalef but included)
✓ Horaire: 9-17 + 20-22 CET tested (Phase 2b, via profiles)
✓ Volatility: ATR bands (Phase 2c, recommended by Mogalef)
✓ Weekday: no Monday/Tuesday (Phase 2d, from PDF)
✓ Independent optimization: each phase locks previous (no cumulative)

## Next Step

After Phase 2 complete: Phase 3 (Exits optimization) using locked Signal + Contexto from Phase 2.
