# COMB_002 IMPULSE — Régimen Dependency Report

- **Fecha análisis:** 2026-04-24 22:35:20
- **Threshold:** PF delta > 50%
- **Régimen dependientes:** 10/12

## 🚨 Combos con Dependencia de Régimen

| Asset | TF | PF_A1 | PF_A2 | PF_A3 | PF_B | Δ% | Patrón |
|-------|-----|-------|-------|-------|-------|-----|--------|
| ES | 10m | 0.87 | 0.76 | 0.54 | 1.07 | 97% | Volatile across periods |
| MNQ | 5m | 0.44 | 1.73 | 1.06 | 1.25 | 290% | Volatile across periods |
| MNQ | 10m | 1.05 | 1.62 | 0.67 | 2.05 | 205% | Volatile across periods |
| MNQ | 15m | 0.76 | 1.55 | 0.81 | 1.94 | 154% | Volatile across periods |
| YM | 5m | 0.87 | 0.76 | 0.54 | 1.07 | 97% | Volatile across periods |
| YM | 10m | 0.92 | 1.02 | 0.52 | 1.62 | 212% | Volatile across periods |
| YM | 15m | 0.66 | 1.03 | 0.44 | 1.92 | 339% | Volatile across periods |
| FDAX | 5m | 0.40 | 2.36 | 6.50 | 1.89 | 1525% | Mal en A, excelente en B (pure recency) |
| FDAX | 10m | 0.21 | 0.42 | 0.48 | 1.29 | 507% | Volatile across periods |
| FDAX | 15m | 0.46 | 0.81 | 0.75 | 3.36 | 630% | Mal en A, excelente en B (pure recency) |

## Recomendaciones

### Para combos con 🚨 Régimen Dependencia:

1. **NO deployar directamente en live** — esperan Phase C (datos post-Mar24) para validar
2. **Re-optimizar con criterio de consistencia:**
   - En lugar de max(PF_B), usar min(PF_A1, PF_A2, PF_A3, PF_B) ≥ 1.0
   - Esto prioriza robustez multi-período sobre peak performance
3. **Añadir filtro de régimen en Phase 2:**
   - Volatility regime: low/medium/high (ATR percentiles)
   - Trend vs Chop: RSI o ADX
   - Optimizar params DISTINTOS por régimen

### Para combos con ✅ Consistencia:

- Candidatos principales para live deployment
- Aún así, validar en Phase C antes de tamaño real
