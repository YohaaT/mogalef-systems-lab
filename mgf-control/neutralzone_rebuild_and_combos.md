PHASE: 2 -> 3 -> exploratory_phase_4_light
OBJECTIVE: Reconstruir `EL_NeutralZone_B_V2`, cerrarlo en PASS con flujo disciplinado completo y rerun de las dos combinaciones desbloqueadas.
SCOPE: Un componente + dos combinaciones exploratorias. Sin abrir Fase 4 definitiva.
INPUTS: `PROJECT_MASTER.md`, `TOKEN_POLICY.md`, `RUN_PROTOCOL.md`, spec/fuente/notas de `EL_NeutralZone_B_V2`, dataset práctico `MNQ 5m`, `EL_STPMT_DIV`, `EL_REPULSE_DIV`.
EXPECTED ARTIFACT: rebuild completo del componente y nota de combinaciones rerun.
STOP CONDITION: detenerse al dejar componente en PASS y combinaciones rerun registradas.

# NeutralZone rebuild and combinations

## 1. Estado del componente
`EL_NeutralZone_B_V2` quedó reconstruido y validado en este run.

### Artefactos del componente
- `mgf-regime-filter-lab/src/EL_NeutralZone_B_V2.py`
- `mgf-regime-filter-lab/tests/EL_NeutralZone_B_V2_test.py`
- `mgf-regime-filter-lab/notes/rebuild_EL_NeutralZone_B_V2.md`
- `mgf-regime-filter-lab/notes/qa_EL_NeutralZone_B_V2.md`
- `mgf-regime-filter-lab/notes/smoke_EL_NeutralZone_B_V2.md`

### Dictamen del componente
- Fase 2: `PASS`
- QA técnica: `PASS`
- Fase 3 smoke: `PASS`
- estado global del componente: `PASS`

## 2. Rerun de combinaciones desbloqueadas
### COMB_004
- combinación: `STPMT_DIV + EL_NeutralZone_B_V2 + stop causal simple`
- estado: `provisional_usable_for_ranking`
- métricas orientativas:
  - trades: `111`
  - wins: `16`
  - losses: `95`
  - net points: `1326.5`
  - avg points: `11.9505`
- interpretación breve:
  - combinación ya usable para ranking provisional;
  - en esta muestra queda competitiva frente a otras ramas ligeras aunque sin usarse como validación fuerte.

### COMB_006
- combinación: `REPULSE_DIV + EL_NeutralZone_B_V2 + stop causal simple`
- estado: `provisional_usable_for_ranking`
- métricas orientativas:
  - trades: `261`
  - wins: `35`
  - losses: `226`
  - net points: `-976.5`
  - avg points: `-3.7414`
- interpretación breve:
  - combinación ya usable para ranking provisional;
  - en esta muestra queda claramente más débil que la rama `STPMT_DIV + EL_NeutralZone_B_V2`.

## 3. Lectura comparativa provisional
Entre las ramas limpias/provisionales probadas hasta ahora:
- `STPMT_DIV + Trend Filter V2 + stop causal simple` sigue bien posicionada para ranking provisional.
- `STPMT_DIV + NeutralZone_B_V2 + stop causal simple` también aparece prometedora a nivel exploratorio.
- `REPULSE_DIV` queda más flojo en ambas ramas probadas hasta ahora.

## 4. Nota metodológica
Estas lecturas siguen siendo exploratorias y comparativas.
No se presentan como validación definitiva de edge.

Result:
Artifacts created:
- rebuild completo de `EL_NeutralZone_B_V2`
- `mgf-control/neutralzone_rebuild_and_combos.md`
- actualización de `mgf-control/combination_registry.md`
Files read:
- `PROJECT_MASTER.md`
- `TOKEN_POLICY.md`
- `RUN_PROTOCOL.md`
- spec/fuente/notas de `EL_NeutralZone_B_V2`
- dataset `MNQ 5m`
Scope respected: yes
Next recommended action: continuar ranking exploratorio de combinaciones ya limpias disponibles.
