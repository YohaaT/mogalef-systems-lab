PHASE: exploratory_phase_4_light
OBJECTIVE: Profundizar la familia `STPMT_DIV` con variaciones sobre `EL_NeutralZone_B_V2` para ranking exploratorio.
SCOPE: Solo combinaciones limpias/provisionales con `STPMT_DIV`, `Trend_Filter_V2`, `NeutralZone_B_V2` y stop causal simple.
INPUTS: dataset `MNQ 5m`, `EL_STPMT_DIV`, `EL_Mogalef_Trend_Filter_V2`, `EL_NeutralZone_B_V2`.
EXPECTED ARTIFACT: `mgf-control/combination_exploration_round_003.md`.
STOP CONDITION: detenerse al registrar esta ronda.

# Combination exploration round 003

## COMB_010
- combinación: `STPMT_DIV + NeutralZone_B_V2(signal) + stop causal simple`
- estado: `provisional_usable_for_ranking`
- métricas orientativas:
  - trades: `3`
  - wins: `0`
  - losses: `3`
  - net points: `-61.0`
  - avg points: `-20.33`
- interpretación breve:
  - extremadamente restrictiva;
  - casi no genera operaciones;
  - no parece útil como rama principal de exploración.

## COMB_011
- combinación: `STPMT_DIV + (Trend_Filter_V2 OR NeutralZone_B_V2(filter)) + stop causal simple`
- estado: `provisional_usable_for_ranking`
- métricas orientativas:
  - trades: `175`
  - wins: `27`
  - losses: `148`
  - net points: `966.0`
  - avg points: `5.52`
- interpretación breve:
  - combinación más permisiva;
  - aumenta bastante la frecuencia;
  - mantiene neto positivo orientativo;
  - útil para ranking provisional como rama amplia de exploración.

## COMB_012
- combinación: `STPMT_DIV + Trend_Filter_V2 + NeutralZone_B_V2(signal) + stop causal simple`
- estado: `provisional_usable_for_ranking`
- métricas orientativas:
  - trades: `1`
  - wins: `0`
  - losses: `1`
  - net points: `-12.5`
  - avg points: `-12.5`
- interpretación breve:
  - demasiado estricta para esta muestra;
  - no aporta valor exploratorio práctico ahora mismo.

## Lectura comparativa de la ronda
Dentro de esta profundización de `STPMT_DIV`:
- `COMB_011` es la rama más útil para ranking provisional.
- `COMB_010` y `COMB_012` son demasiado restrictivas para esta muestra.

## Lectura global provisional actual de la familia STPMT
Ramas mejor posicionadas para exploración:
1. `COMB_001` -> `STPMT_DIV + Trend_Filter_V2`
2. `COMB_004` -> `STPMT_DIV + NeutralZone_B_V2`
3. `COMB_007` -> `STPMT_DIV + Trend_Filter_V2 + NeutralZone_B_V2`
4. `COMB_011` -> `STPMT_DIV + (Trend_Filter_V2 OR NeutralZone_B_V2)`

Result:
Artifacts created:
- `mgf-control/combination_exploration_round_003.md`
Files read:
- dataset `MNQ 5m`
- `EL_STPMT_DIV`
- `EL_Mogalef_Trend_Filter_V2`
- `EL_NeutralZone_B_V2`
Scope respected: yes
Next recommended action: consolidar ranking provisional de la familia `STPMT_DIV` y decidir si merece una fase de exploración horaria por combinación.
