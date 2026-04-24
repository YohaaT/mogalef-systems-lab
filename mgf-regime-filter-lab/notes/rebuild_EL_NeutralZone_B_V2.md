PHASE: 2
OBJECTIVE: Reconstruir `EL_NeutralZone_B_V2` en Python reproducible.
SCOPE: Un componente. Sin combinaciones ni backtests en este run de rebuild.
INPUTS: `PROJECT_MASTER.md`, `TOKEN_POLICY.md`, `RUN_PROTOCOL.md`, `mgf-regime-filter-lab/spec/EL_NeutralZone_B_V2.md`, `mgf-regime-filter-lab/neutral-zone/EL_NeutralZone_B_V2.txt`, `mgf-regime-filter-lab/notes/EL_NeutralZone_B_V2_ambiguities.md`.
EXPECTED ARTIFACT: `mgf-regime-filter-lab/src/EL_NeutralZone_B_V2.py`, `mgf-regime-filter-lab/tests/EL_NeutralZone_B_V2_test.py`, `mgf-regime-filter-lab/notes/rebuild_EL_NeutralZone_B_V2.md`.
STOP CONDITION: detenerse al dejar el rebuild persistido.

# Rebuild EL_NeutralZone_B_V2

## Decisiones de traducción
- Se preserva el recorrido retrospectivo del componente para replicar el comportamiento original de marcadores y pulsos en modo `signal`.
- `VueTrend=Yes` se interpreta como `vue_trend=True`, coherente con la ambigüedad documentada.
- `ret_mid` se usa como nombre Python del eje estructural para evitar conflicto con `RET` parámetro/serie del fuente.
- En la última barra, el sentimiento queda en `50` por no existir referencia `i+1` válida para transición retrospectiva.

## Cobertura del rebuild
- modo `filter`
- modo `signal`
- inversión por `sens`
- banda de tendencia visible
- marcadores `marqueurRET` y `marqueurMME`

## Riesgo conocido
La lógica sigue siendo retrospectiva como el fuente. Esto es correcto para rebuild del componente, pero en uso de estrategia puede requerir etiquetado causal aparte.

Result:
Artifacts created:
- `mgf-regime-filter-lab/src/EL_NeutralZone_B_V2.py`
- `mgf-regime-filter-lab/tests/EL_NeutralZone_B_V2_test.py`
- `mgf-regime-filter-lab/notes/rebuild_EL_NeutralZone_B_V2.md`
Files read:
- `PROJECT_MASTER.md`
- `TOKEN_POLICY.md`
- `RUN_PROTOCOL.md`
- `mgf-regime-filter-lab/spec/EL_NeutralZone_B_V2.md`
- `mgf-regime-filter-lab/neutral-zone/EL_NeutralZone_B_V2.txt`
- `mgf-regime-filter-lab/notes/EL_NeutralZone_B_V2_ambiguities.md`
Scope respected: yes
Next recommended action: QA técnica breve del componente reconstruido.
