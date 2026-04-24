# Rebuild EL_Stop_Intelligent

PHASE: 2
OBJECTIVE: Reconstruir únicamente `EL_Stop_Intelligent` en Python reproducible.
SCOPE: Un solo componente. Sin QA en este run, sin smoke test, sin backtest, sin tocar otros componentes.
INPUTS: PROJECT_MASTER.md, TOKEN_POLICY.md, RUN_PROTOCOL.md, `mgf-stop-lab/spec/EL_Stop_Intelligent.md`, `mgf-stop-lab/intelligent-family/EL_Stop_Intelligent.txt`, `mgf-control/phase_state.json`.
EXPECTED ARTIFACT: `mgf-stop-lab/src/EL_Stop_Intelligent.py`, `mgf-stop-lab/tests/EL_Stop_Intelligent_test.py`, `mgf-stop-lab/notes/rebuild_EL_Stop_Intelligent.md`, actualización de `mgf-control/session_checkpoint.md`, `mgf-control/night_run_summary.md`, `mgf-control/phase_state.json`.
STOP CONDITION: detenerse al completar esos artefactos.

## Fuente funcional principal
- `mgf-stop-lab/spec/EL_Stop_Intelligent.md`

## Fuente de contraste
- `mgf-stop-lab/intelligent-family/EL_Stop_Intelligent.txt`

## Resultado del run
Reconstrucción completada sin abrir `Fase 3`.

## Decisiones de traducción aplicadas
- Se usó la spec como definición funcional principal y el fuente original solo como contraste de fidelidad.
- Se mantuvo la orientación retrospectiva de los pivots recorriendo las series de derecha a izquierda, igual que en el original.
- Se preservó la lógica de `space` tal cual, incluyendo la posibilidad de valor negativo y el uso de `abs(...)` solo en los clamps defensivos.
- Se preservó la memoria implícita de `flaglong`: al quedar flat no se fuerza reset agresivo; la serie conserva la última dirección observada dentro del recorrido retrospectivo.
- Se mantuvo una sola serie funcional de stop (`stop`) para ambos lados, reflejando la reutilización de `stoplong` en el fuente original.
- Se dejaron `None` en barras sin historia suficiente para ATR de referencia, pivots o base de stop válida.
- La lógica `WaitForXtrem` se implementó de forma literal según el fuente base, sin incorporar correcciones operativas de la variante live.

## Ambigüedades críticas
No apareció una ambigüedad crítica que impidiera una reconstrucción honesta dentro del alcance de este run.

## Cobertura mínima añadida
- persistencia de `None` cuando aún no existe volatilidad de referencia suficiente;
- monotonicidad del stop largo una vez ajustado;
- congelación del stop largo bajo `WaitForXtrem` hasta ruptura del extremo almacenado.

## Qué no se hizo
- No se hizo QA.
- No se hizo smoke test.
- No se hizo backtest.
- No se tocaron otros componentes.
- No se abrió `Fase 3`.

Result:
Artifacts created:
- `mgf-stop-lab/src/EL_Stop_Intelligent.py`
- `mgf-stop-lab/tests/EL_Stop_Intelligent_test.py`
- `mgf-stop-lab/notes/rebuild_EL_Stop_Intelligent.md`
- `mgf-control/session_checkpoint.md`
- `mgf-control/night_run_summary.md`
- `mgf-control/phase_state.json`
Files read:
- PROJECT_MASTER.md
- TOKEN_POLICY.md
- RUN_PROTOCOL.md
- `mgf-stop-lab/spec/EL_Stop_Intelligent.md`
- `mgf-stop-lab/intelligent-family/EL_Stop_Intelligent.txt`
- `mgf-control/phase_state.json`
Scope respected: yes
Next recommended action: QA técnica breve únicamente sobre `EL_Stop_Intelligent`.
