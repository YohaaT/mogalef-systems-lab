PHASE: exploratory_phase_4_light
OBJECTIVE: Ejecutar la siguiente ronda limpia/provisional de combinaciones para ranking exploratorio relativo.
SCOPE: Solo combinaciones limpias con `STPMT_DIV`, `REPULSE_DIV`, `Trend_Filter_V2`, `NeutralZone_B_V2` y stop causal simple.
INPUTS: `mgf-control/combination_registry.md`, dataset `MNQ 5m`, implementaciones limpias disponibles.
EXPECTED ARTIFACT: `mgf-control/combination_exploration_round_002.md`.
STOP CONDITION: detenerse al registrar esta ronda.

# Combination exploration round 002

## COMB_007
- combinación: `STPMT_DIV + Trend_Filter_V2 + NeutralZone_B_V2 + stop causal simple`
- estado: `provisional_usable_for_ranking`
- métricas orientativas:
  - trades: `64`
  - wins: `4`
  - losses: `60`
  - net points: `357.75`
  - avg points: `5.5898`
- interpretación breve:
  - el doble filtro reduce bastante la frecuencia;
  - mantiene neto positivo pequeño en la muestra;
  - queda detrás de otras ramas STPMT más simples, pero sigue siendo usable para ranking provisional.

## COMB_008
- combinación: `REPULSE_DIV + Trend_Filter_V2 + NeutralZone_B_V2 + stop causal simple`
- estado: `provisional_usable_for_ranking`
- métricas orientativas:
  - trades: `167`
  - wins: `6`
  - losses: `161`
  - net points: `-2014.0`
  - avg points: `-12.0599`
- interpretación breve:
  - combinación limpia pero claramente débil en esta muestra;
  - queda mal posicionada para ranking provisional.

## COMB_009
- combinación: consenso `STPMT_DIV + REPULSE_DIV + Trend_Filter_V2 + stop causal simple`
- estado: `provisional_usable_for_ranking`
- métricas orientativas:
  - trades: `15`
  - wins: `1`
  - losses: `14`
  - net points: `-472.5`
  - avg points: `-31.5`
- interpretación breve:
  - la exigencia de consenso reduce drásticamente señales;
  - en esta muestra no parece mejorar el comportamiento exploratorio.

## Lectura comparativa de la ronda
Dentro de esta tanda:
- `COMB_007` es la que mejor aguanta para ranking provisional.
- `COMB_008` y `COMB_009` quedan claramente por detrás.

## Lectura comparativa global provisional
Siguen bien posicionadas para ranking provisional:
1. `COMB_001` -> `STPMT_DIV + Trend_Filter_V2 + stop causal simple`
2. `COMB_004` -> `STPMT_DIV + NeutralZone_B_V2 + stop causal simple`
3. `COMB_007` -> `STPMT_DIV + Trend_Filter_V2 + NeutralZone_B_V2 + stop causal simple`

Las ramas con `REPULSE_DIV` siguen quedando por detrás en esta muestra.

Result:
Artifacts created:
- `mgf-control/combination_exploration_round_002.md`
Files read:
- `mgf-control/combination_registry.md`
- dataset `MNQ 5m`
- implementaciones limpias disponibles
Scope respected: yes
Next recommended action: seguir profundizando primero en la familia `STPMT_DIV` antes de dedicar más coste a ramas `REPULSE_DIV`.
