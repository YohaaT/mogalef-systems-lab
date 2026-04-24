# Rebuild EL_Mogalef_Trend_Filter_V2

PHASE: 2
OBJECTIVE: Reconstruir únicamente `EL_Mogalef_Trend_Filter_V2` en Python reproducible.
SCOPE: Un solo componente. Sin QA en este run, sin smoke test, sin backtest, sin tocar otros componentes.
INPUTS: PROJECT_MASTER.md, TOKEN_POLICY.md, RUN_PROTOCOL.md, `mgf-regime-filter-lab/spec/EL_Mogalef_Trend_Filter_V2.md`, `mgf-regime-filter-lab/trend-overlays/EL_Mogalef_Trend_Filter_V2.txt`, `mgf-control/phase_state.json`.
EXPECTED ARTIFACT: `mgf-regime-filter-lab/src/EL_Mogalef_Trend_Filter_V2.py`, `mgf-regime-filter-lab/tests/EL_Mogalef_Trend_Filter_V2_test.py`, `mgf-regime-filter-lab/notes/rebuild_EL_Mogalef_Trend_Filter_V2.md`, actualización de `mgf-control/session_checkpoint.md`, `mgf-control/night_run_summary.md`, `mgf-control/phase_state.json`.
STOP CONDITION: detenerse al completar esos artefactos.

## Fuente funcional principal
- `mgf-regime-filter-lab/spec/EL_Mogalef_Trend_Filter_V2.md`

## Fuente de contraste
- `mgf-regime-filter-lab/trend-overlays/EL_Mogalef_Trend_Filter_V2.txt`

## Resultado del run
Reconstrucción completada sin abrir `Fase 3`.

## Decisiones de traducción aplicadas
- Se usó la spec como definición funcional principal y el fuente original solo como contraste de fidelidad.
- La traducción quedó en orientación cronológica normal, preservando el desplazamiento `open[length-1 barras atrás]` como `open_[i - (length - 1)]`.
- El cálculo de repulse se implementó con `rolling low`, `rolling high` y EMA separadas para tramo alcista y bajista, igualando la estructura observada en el fuente.
- Los empates de pendiente se mantienen literalmente del lado `-1`, sin estado neutro.
- La regla `CurrentBarIndex() < R3*5` se preservó como gate duro que deja `CAS=None` y `sentiment="block"` hasta historia suficiente.
- La caducidad posterior al 2030-12-05 se mantuvo como kill-switch observable y quedó aislada en un helper para poder parametrizarla después sin tocar el núcleo del filtro.
- La ambigüedad del host sobre `sentiment` por defecto se resolvió de forma explícita: barras válidas arrancan en `pass` salvo que la política de bloqueo las bloquee; barras con `CAS=None` permanecen en `block`.
- `OffOn=0` se resolvió como filtro desactivado para barras válidas, dejando pasar sin arrastrar estado previo del host.

## Ambigüedades críticas
No apareció una ambigüedad crítica que impidiera una reconstrucción honesta dentro del alcance de este run.

## Cobertura mínima añadida
- gate de historia mínima `R3*5`;
- validación explícita del mapeo observado del sample monotónico al `Case 1`;
- bloqueo por `blocked_cases`;
- modo `TradeOnlyThisCASE`;
- bypass con `OffOn=0`;
- kill-switch de fecha que fuerza `CAS=0`.

## Corrección posterior aplicada
- el branch del kill-switch por fecha ya no hace `continue` ni fuerza `sentiment="pass"`;
- cuando la fecha supera el corte, el rebuild fija `CAS=0` y luego deja que la política normal de interpretación decida `pass` o `block`;
- se añadió test mínimo para verificar que `TradeOnlyThisCASE` bloquea correctamente una barra post-corte con `CAS=0`.

## Qué no se hizo
- No se hizo QA.
- No se hizo smoke test.
- No se hizo backtest.
- No se tocaron otros componentes.
- No se abrió `Fase 3`.

Result:
Artifacts created:
- `mgf-regime-filter-lab/src/EL_Mogalef_Trend_Filter_V2.py`
- `mgf-regime-filter-lab/tests/EL_Mogalef_Trend_Filter_V2_test.py`
- `mgf-regime-filter-lab/notes/rebuild_EL_Mogalef_Trend_Filter_V2.md`
- `mgf-control/session_checkpoint.md`
- `mgf-control/night_run_summary.md`
- `mgf-control/phase_state.json`
Files read:
- PROJECT_MASTER.md
- TOKEN_POLICY.md
- RUN_PROTOCOL.md
- `mgf-regime-filter-lab/spec/EL_Mogalef_Trend_Filter_V2.md`
- `mgf-regime-filter-lab/trend-overlays/EL_Mogalef_Trend_Filter_V2.txt`
- `mgf-control/phase_state.json`
Scope respected: yes
Next recommended action: QA técnica breve únicamente sobre `EL_Mogalef_Trend_Filter_V2`.
