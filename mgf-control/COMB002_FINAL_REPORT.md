# COMB_002_IMPULSE — Informe Final Consolidado

- **Fecha consolidación:** 2026-04-24
- **Fecha reporte:**       2026-04-24
- **Método:**              sequential_vs_cross_validation
- **Thresholds:**          Rob ≥ 0.8 · Trades ≥ 30 · Tie Δ = 0.05

---

## Conteo global

- **Total combos:** 12
- **Approach ganador:** sequential=6 · cross=6 · none=0
- **Status final:** ✅ OK=12 · ⚠️ DEGRADED=0 · ❌ MISSING=0
- **Pasan rob ≥ 0.8:** 12/12
- **Pasan trades ≥ 30 (Phase A):** 12/12

---

## Tabla resumen — ganadores por asset/timeframe

| Asset | TF | Status | Winner | Rob | PF_A | PF_B | T_A | T_B | Δ vs loser |
|-------|-----|--------|--------|------|------|------|-----|-----|------------|
| ES | 5m | ✅ | cross | 1.6252 | 1.0325 | 1.6779 | 137 | 93 | -120.6181 |
| ES | 10m | ✅ | cross | 1.9227 | 0.7496 | 1.4413 | 204 | 114 | +0.1343 |
| ES | 15m | ✅ | cross | 0.9631 | 1.1115 | 1.0706 | 109 | 71 | -2.7334 |
| MNQ | 5m | ✅ | cross | 2.1111 | 0.7021 | 1.4822 | 98 | 85 | -4.2356 |
| MNQ | 10m | ✅ | sequential | 1.8567 | 1.1024 | 2.0468 | 85 | 64 | -0.0706 |
| MNQ | 15m | ✅ | sequential | 2.0844 | 0.9296 | 1.9378 | 91 | 69 | -0.1721 |
| YM | 5m | ✅ | cross | 1.9227 | 0.7496 | 1.4413 | 204 | 114 | -1.7738 |
| YM | 10m | ✅ | sequential | 2.0046 | 0.8073 | 1.6183 | 219 | 155 | -0.1595 |
| YM | 15m | ✅ | sequential | 2.7084 | 0.7088 | 1.9196 | 81 | 69 | -1.1331 |
| FDAX | 5m | ✅ | cross | 1.8066 | 1.0458 | 1.8894 | 48 | 49 | -3.2249 |
| FDAX | 10m | ✅ | sequential | 3.7668 | 0.3412 | 1.2851 | 58 | 52 | -1.3378 |
| FDAX | 15m | ✅ | sequential | 4.9831 | 0.6748 | 3.3625 | 57 | 31 | -2.1630 |

---

## Parámetros finales por combo

| Asset | TF | smooth_h/b | dist_h/l | horaire | volat | scalp_coef | ts | stop_q | stop_coef |
|-------|-----|------------|----------|---------|-------|------------|-----|--------|-----------|
| ES | 5m | 5/1 | 25/25 | Mogalef_V2_CEST_18_20 | no_filter_0_500 | 1.5 | 20 | 1 | 3.0 |
| ES | 10m | 1/5 | 25/25 | US_regular_9_15 | no_filter_0_500 | 5.0 | 10 | 1 | 4.0 |
| ES | 15m | 5/5 | 75/25 | NY_afternoon_12_16 | no_filter_0_500 | 1.5 | 12 | 1 | 5.0 |
| MNQ | 5m | 1/5 | 25/25 | NY_afternoon_12_16 | selective_20_200 | 5.0 | 10 | 1 | 3.0 |
| MNQ | 10m | 5/2 | 25/25 | NY_afternoon_12_16 | selective_20_200 | 2.0 | 20 | 1 | 2.0 |
| MNQ | 15m | 5/5 | 25/75 | Mogalef_V1_CEST_7_15 | selective_20_200 | 1.5 | 10 | 1 | 3.0 |
| YM | 5m | 1/5 | 25/25 | US_regular_9_15 | no_filter_0_500 | 5.0 | 10 | 1 | 4.0 |
| YM | 10m | 3/1 | 75/25 | US_regular_9_15 | min_floor_10_500 | 5.0 | 18 | 1 | 2.0 |
| YM | 15m | 5/1 | 25/25 | NY_afternoon_12_16 | selective_20_200 | 4.0 | 20 | 1 | 3.0 |
| FDAX | 5m | 4/5 | 75/25 | 24h_no_filter | selective_20_200 | 5.0 | 15 | 1 | 3.0 |
| FDAX | 10m | 3/5 | 25/75 | US_regular_9_15 | selective_20_200 | 5.0 | 10 | 1 | 2.0 |
| FDAX | 15m | 5/4 | 75/25 | NY_morning_9_12 | no_filter_0_500 | 4.0 | 15 | 1 | 5.0 |

---

## Detalle de decisión por combo

### ✅ ES 5m

- **Winner:** `cross`
- **Motivo:** only cross passes all filters
- **Sequential Rob:** 122.2433
- **Cross Rob:** 1.6252
- **Δ (cross − seq):** -120.6181
- **Final Rob:** 1.6252 (PF_A=1.0325 · PF_B=1.6779)
- **Trades:** A=137 · B=93
- **Filtros:** rob_pass=✓ · trades_pass=✓

### ✅ ES 10m

- **Winner:** `cross`
- **Motivo:** cross wins by +0.1343 robustness
- **Sequential Rob:** 1.7884
- **Cross Rob:** 1.9227
- **Δ (cross − seq):** 0.1343
- **Final Rob:** 1.9227 (PF_A=0.7496 · PF_B=1.4413)
- **Trades:** A=204 · B=114
- **Filtros:** rob_pass=✓ · trades_pass=✓

### ✅ ES 15m

- **Winner:** `cross`
- **Motivo:** only cross passes all filters
- **Sequential Rob:** 3.6965
- **Cross Rob:** 0.9631
- **Δ (cross − seq):** -2.7334
- **Final Rob:** 0.9631 (PF_A=1.1115 · PF_B=1.0706)
- **Trades:** A=109 · B=71
- **Filtros:** rob_pass=✓ · trades_pass=✓

### ✅ MNQ 5m

- **Winner:** `cross`
- **Motivo:** only cross passes all filters
- **Sequential Rob:** 6.3467
- **Cross Rob:** 2.1111
- **Δ (cross − seq):** -4.2356
- **Final Rob:** 2.1111 (PF_A=0.7021 · PF_B=1.4822)
- **Trades:** A=98 · B=85
- **Filtros:** rob_pass=✓ · trades_pass=✓

### ✅ MNQ 10m

- **Winner:** `sequential`
- **Motivo:** sequential wins by +0.0706 robustness
- **Sequential Rob:** 1.8567
- **Cross Rob:** 1.7861
- **Δ (cross − seq):** -0.0706
- **Final Rob:** 1.8567 (PF_A=1.1024 · PF_B=2.0468)
- **Trades:** A=85 · B=64
- **Filtros:** rob_pass=✓ · trades_pass=✓

### ✅ MNQ 15m

- **Winner:** `sequential`
- **Motivo:** sequential wins by +0.1721 robustness
- **Sequential Rob:** 2.0844
- **Cross Rob:** 1.9123
- **Δ (cross − seq):** -0.1721
- **Final Rob:** 2.0844 (PF_A=0.9296 · PF_B=1.9378)
- **Trades:** A=91 · B=69
- **Filtros:** rob_pass=✓ · trades_pass=✓

### ✅ YM 5m

- **Winner:** `cross`
- **Motivo:** only cross passes all filters
- **Sequential Rob:** 3.6965
- **Cross Rob:** 1.9227
- **Δ (cross − seq):** -1.7738
- **Final Rob:** 1.9227 (PF_A=0.7496 · PF_B=1.4413)
- **Trades:** A=204 · B=114
- **Filtros:** rob_pass=✓ · trades_pass=✓

### ✅ YM 10m

- **Winner:** `sequential`
- **Motivo:** sequential wins by +0.1595 robustness
- **Sequential Rob:** 2.0046
- **Cross Rob:** 1.8451
- **Δ (cross − seq):** -0.1595
- **Final Rob:** 2.0046 (PF_A=0.8073 · PF_B=1.6183)
- **Trades:** A=219 · B=155
- **Filtros:** rob_pass=✓ · trades_pass=✓

### ✅ YM 15m

- **Winner:** `sequential`
- **Motivo:** sequential wins by +1.1331 robustness
- **Sequential Rob:** 2.7084
- **Cross Rob:** 1.5753
- **Δ (cross − seq):** -1.1331
- **Final Rob:** 2.7084 (PF_A=0.7088 · PF_B=1.9196)
- **Trades:** A=81 · B=69
- **Filtros:** rob_pass=✓ · trades_pass=✓

### ✅ FDAX 5m

- **Winner:** `cross`
- **Motivo:** only cross passes all filters
- **Sequential Rob:** 5.0315
- **Cross Rob:** 1.8066
- **Δ (cross − seq):** -3.2249
- **Final Rob:** 1.8066 (PF_A=1.0458 · PF_B=1.8894)
- **Trades:** A=48 · B=49
- **Filtros:** rob_pass=✓ · trades_pass=✓

### ✅ FDAX 10m

- **Winner:** `sequential`
- **Motivo:** sequential wins by +1.3378 robustness
- **Sequential Rob:** 3.7668
- **Cross Rob:** 2.4290
- **Δ (cross − seq):** -1.3378
- **Final Rob:** 3.7668 (PF_A=0.3412 · PF_B=1.2851)
- **Trades:** A=58 · B=52
- **Filtros:** rob_pass=✓ · trades_pass=✓

### ✅ FDAX 15m

- **Winner:** `sequential`
- **Motivo:** sequential wins by +2.1630 robustness
- **Sequential Rob:** 4.9831
- **Cross Rob:** 2.8201
- **Δ (cross − seq):** -2.1630
- **Final Rob:** 4.9831 (PF_A=0.6748 · PF_B=3.3625)
- **Trades:** A=57 · B=31
- **Filtros:** rob_pass=✓ · trades_pass=✓

---

## Alertas

_Ningún combo degradado o faltante — todos los 12 pasan filtros._

---

## Recomendaciones operacionales

1. **Deploy en live:** Solo los 12 combos con status ✅ OK están listos.
2. **Sizing inicial:** Comenzar con tamaño reducido (25-50% del riesgo target) durante los primeros 30 días.
3. **Hold-out validation:** Antes de escalar, correr los FINAL_PARAMS sobre los últimos 3 meses (datos no usados en Phase A/B).
4. **Monitoreo:** Alertar si el PF live cae por debajo del 70% del PF_B esperado durante 2 semanas consecutivas.
5. **Degraded combos:** Re-optimizar con más datos o abandonar; no usar en live.
6. **Re-optimización periódica:** Cada 6 meses repetir Phases 1-5 con ventanas actualizadas.
