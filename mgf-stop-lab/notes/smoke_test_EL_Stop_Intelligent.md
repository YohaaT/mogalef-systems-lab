# Smoke test EL_Stop_Intelligent

PHASE: 3
OBJECTIVE: Ejecutar smoke test únicamente sobre `EL_Stop_Intelligent` tras `PASS` en Fase 2, usando la nueva regla de gate automático `Fase 2 -> Fase 3` para componentes individuales.
SCOPE: Un solo componente. Sin backtest, sin otros componentes, sin abrir `Fase 4`.
INPUTS: PROJECT_MASTER.md, TOKEN_POLICY.md, RUN_PROTOCOL.md, `mgf-control/phase_state.json`, `mgf-stop-lab/spec/EL_Stop_Intelligent.md`, `mgf-stop-lab/src/EL_Stop_Intelligent.py`, `mgf-stop-lab/tests/EL_Stop_Intelligent_test.py`, `mgf-stop-lab/notes/rebuild_EL_Stop_Intelligent.md`.
EXPECTED ARTIFACT: `mgf-stop-lab/notes/smoke_test_EL_Stop_Intelligent.md`, `mgf-stop-lab/outputs/smoke_test_EL_Stop_Intelligent/`, actualización de `mgf-control/phase_state.json`, `mgf-control/approval_request.md`, `mgf-control/approval_queue.md`, `mgf-control/session_checkpoint.md`, `mgf-control/night_run_summary.md`.
STOP CONDITION: detenerse al persistir el resultado del smoke.

## Resultado
PASS.

## Checks ejecutados
- monotonicidad del stop largo una vez activo
- congelación por `WaitForXtrem` en largo
- monotonicidad del stop corto una vez activo

## Dictamen
- no apareció incoherencia operativa mínima en el componente;
- el smoke pasa dentro del alcance autorizado de `Fase 3`;
- no se abre `Fase 4`.

## Artefactos de salida
- `mgf-stop-lab/outputs/smoke_test_EL_Stop_Intelligent/case_long_monotonic.json`
- `mgf-stop-lab/outputs/smoke_test_EL_Stop_Intelligent/case_wait_long.json`
- `mgf-stop-lab/outputs/smoke_test_EL_Stop_Intelligent/case_short_monotonic.json`
- `mgf-stop-lab/outputs/smoke_test_EL_Stop_Intelligent/smoke_checks.csv`
- `mgf-stop-lab/outputs/smoke_test_EL_Stop_Intelligent/summary.json`

## Qué no se hizo
- No se hizo backtest.
- No se abrió `Fase 4`.
- No se tocaron otros componentes.

Result:
Artifacts created:
- `mgf-stop-lab/notes/smoke_test_EL_Stop_Intelligent.md`
- `mgf-stop-lab/outputs/smoke_test_EL_Stop_Intelligent/`
- `mgf-control/phase_state.json`
- `mgf-control/approval_request.md`
- `mgf-control/approval_queue.md`
- `mgf-control/session_checkpoint.md`
- `mgf-control/night_run_summary.md`
Files read:
- PROJECT_MASTER.md
- TOKEN_POLICY.md
- RUN_PROTOCOL.md
- `mgf-control/phase_state.json`
- `mgf-stop-lab/notes/rebuild_EL_Stop_Intelligent.md`
- `mgf-stop-lab/src/EL_Stop_Intelligent.py`
- `mgf-stop-lab/tests/EL_Stop_Intelligent_test.py`
Scope respected: yes
Next recommended action: preparar automáticamente la siguiente unidad válida, `Fase 2` para `EL_Mogalef_Trend_Filter_V2`.
