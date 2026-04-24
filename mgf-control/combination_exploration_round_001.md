PHASE: exploratory_phase_4_light
OBJECTIVE: Probar la siguiente tanda de combinaciones priorizadas para ranking exploratorio relativo, sin tratar métricas como validación fuerte.
SCOPE: `STPMT_DIV` y `REPULSE_DIV` con `Trend_Filter_V2` y `NeutralZone_B_V2` cuando exista implementación usable. Sin abrir validación seria definitiva.
INPUTS: `mgf-control/combination_exploration_policy.md`, `mgf-control/combination_registry.md`, `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`, implementaciones disponibles de `EL_STPMT_DIV`, `EL_REPULSE_DIV`, `EL_Mogalef_Trend_Filter_V2`.
EXPECTED ARTIFACT: `mgf-control/combination_exploration_round_001.md`.
STOP CONDITION: detenerse al registrar esta ronda exploratoria.

# Combination exploration round 001

## Combinaciones evaluadas o bloqueadas

### COMB_004
- combinación: `STPMT_DIV + EL_NeutralZone_B_V2`
- estado: `blocked_for_strategy_use`
- motivo: no existe implementación Python usable de `EL_NeutralZone_B_V2` en `src`, solo spec/txt/notas.

### COMB_005
- combinación: `REPULSE_DIV + EL_Mogalef_Trend_Filter_V2 + stop causal simple`
- estado: `provisional_usable_for_ranking`
- métricas orientativas observadas:
  - trades: `227`
  - wins: `35`
  - losses: `192`
  - net points: `49.5`
  - avg points: `0.2181`
- interpretación breve:
  - combinación usable para ranking exploratorio;
  - en esta muestra parece claramente menos prometedora que `STPMT_DIV + Trend Filter V2 + stop causal simple`;
  - no se interpreta como evidencia final de edge ni como rechazo definitivo.

### COMB_006
- combinación: `REPULSE_DIV + EL_NeutralZone_B_V2`
- estado: `blocked_for_strategy_use`
- motivo: misma inconsistencia real, falta rebuild Python usable de `EL_NeutralZone_B_V2`.

## Lectura comparativa de esta ronda
- `STPMT_DIV + Trend Filter V2` sigue apareciendo mejor posicionada para ranking provisional.
- `REPULSE_DIV + Trend Filter V2` queda por detrás en esta muestra reciente.
- `NeutralZone_B_V2` no puede entrar todavía en comparación operativa por falta de implementación usable.

## Conclusión de la ronda
La exploración puede seguir avanzando sin detenerse por métricas imperfectas.
El bloqueo real aquí no es metodológico sino de implementación faltante para `NeutralZone_B_V2`.

Result:
Artifacts created:
- `mgf-control/combination_exploration_round_001.md`
Files read:
- `mgf-control/combination_exploration_policy.md`
- `mgf-control/combination_registry.md`
- `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`
- implementaciones disponibles de `EL_STPMT_DIV`, `EL_REPULSE_DIV`, `EL_Mogalef_Trend_Filter_V2`
Scope respected: yes
Next recommended action: decidir si se reconstruye `EL_NeutralZone_B_V2` para desbloquear más combinaciones o si se sigue explorando otras combinaciones ya implementadas.
