# Workflow operating mode

PHASE: control
OBJECTIVE: Fijar modo operativo híbrido con orquestación central y subagentes especializados para `mogalef-systems-lab`.
SCOPE: Archivos de control del workflow únicamente. Sin abrir fase nueva y sin abrir una unidad técnica nueva en este mismo cambio.
INPUTS: PROJECT_MASTER.md, TOKEN_POLICY.md, RUN_PROTOCOL.md, `mgf-control/phase_state.json`, `mgf-control/approval_queue.md`, `mgf-control/approval_request.md`, `mgf-control/session_checkpoint.md`, `mgf-control/night_run_summary.md`.
EXPECTED ARTIFACT: `mgf-control/workflow_operating_mode.md`, actualización de `phase_state.json`, `session_checkpoint.md` y `night_run_summary.md`.
STOP CONDITION: Detenerse al persistir el nuevo modo operativo.

## Principio rector
`bo` sigue siendo el cerebro, el orquestador y el dueño del estado.
Los subagentes se usan solo cuando aportan aislamiento, especialización o mejor control de calidad.
No se usan subagentes para todo.
El usuario no debe actuar como mensajero entre fases o agentes.

## Fuente de verdad obligatoria
Leer y respetar siempre:
- `PROJECT_MASTER.md`
- `TOKEN_POLICY.md`
- `RUN_PROTOCOL.md`
- `mgf-control/phase_state.json`
- `mgf-control/approval_queue.md`
- `mgf-control/approval_request.md`
- `mgf-control/session_checkpoint.md`
- `mgf-control/night_run_summary.md`

## Regla simple de asignación de trabajo

### 1. Trabajo pequeño, lineal y barato -> `bo`
Ejemplos:
- sincronizar estado
- cerrar o abrir gates
- decidir la siguiente unidad válida
- preparar `approval_request`
- consolidar resultados
- actualizar checkpoint y resumen
- tareas administrativas del workflow

### 2. Build real -> `sa-build`
Ejemplos:
- reconstrucción Python de un componente
- corrección técnica del código
- ajuste de tests cuando forme parte de una unidad de build

### 3. QA documental o técnica -> `sa-qa`
Ejemplos:
- QA de specs
- QA de implementación
- re-QA
- smoke test review
- comprobación de fidelidad spec -> código -> test

### 4. Análisis de discrepancia o dictamen -> `sa-review`
Ejemplos:
- distinguir `TEST_FIX` vs `CODE_FIX` vs `SPEC_FIX`
- decidir si un fallo viene del smoke, del código o de la spec
- emitir dictamen `PASS` / `FIX` / `BLOCK` cuando convenga una revisión separada

### 5. Research faltante -> `sa-research`
Usarlo solo si falta información esencial.
No usar `sa-research` si ya bastan:
- spec
- código fuente
- QA previa
- reportes existentes
- estado persistente del proyecto

## Reglas de uso de subagentes
- usar como máximo un subagente por unidad principal cuando sea suficiente;
- no abrir ramas paralelas innecesarias;
- no lanzar subagentes para microtareas administrativas;
- cada subagente debe dejar artefactos persistentes en disco;
- `bo` consolida siempre el resultado en `phase_state.json`, `session_checkpoint.md` y `night_run_summary.md`;
- si una unidad no justifica especialista, la hace `bo`.

## Reglas de fases y gates
- `Fase 2 -> Fase 3` está autorizada automáticamente para componentes individuales;
- `Fase 3 -> Fase 4` sigue requiriendo aprobación explícita;
- pedir aprobación solo para:
  - `Fase 3 -> Fase 4`
  - bloqueos reales
  - trabajo caro o sensible
  - cambios de arquitectura
  - uso de videos
  - backtests

## Reglas de coste
- aplicar `TOKEN_POLICY.md` estrictamente;
- minimizar tokens;
- no releer material bruto si ya existe spec o resumen suficiente;
- no hacer QA y corrección en el mismo run salvo error crítico trivial;
- no usar el chat como memoria del proyecto.

## Regla autónoma actualizada
La sincronización administrativa de estado por sí sola no cuenta como la única unidad válida del run, salvo que:
- revele un gate real;
- revele `awaiting_user_approval`;
- o revele un bloqueo real.

Si el run detecta y corrige una inconsistencia administrativa menor en:
- `phase_state.json`
- `approval_request.md`
- `approval_queue.md`
- `session_checkpoint.md`
- `night_run_summary.md`

entonces debe:
1. corregirla;
2. persistir el estado;
3. reevaluar inmediatamente la siguiente unidad técnica válida;
4. continuar con esa unidad técnica en el mismo run si no existe gate, approval wait o bloqueo real.

## Regla operativa de prioridad
- prioridad 1: coherencia de estado
- prioridad 2: unidad técnica válida
- la unidad administrativa no debe consumir el run completo salvo que detenga legítimamente el workflow

## Prioridad actual del proyecto
1. `EL_STPMT_DIV`
2. `EL_REPULSE_DIV`

Ambos deben trabajarse desde `Fase 2`, sin rehacer `Fase 0` ni `Fase 1`, salvo bloqueo real o inconsistencia documentada.

## Estado operativo inmediato
La arquitectura híbrida se adopta desde el siguiente run automático del cron.
La siguiente unidad válida ya pendiente en `phase_state.json` es:
- `Fase 2` fix de `EL_STPMT_DIV`, seguido de re-QA en run separado

Result:
Artifacts created:
- `mgf-control/workflow_operating_mode.md`
- `mgf-control/phase_state.json`
- `mgf-control/session_checkpoint.md`
- `mgf-control/night_run_summary.md`
Files read:
- `mgf-control/phase_state.json`
- `mgf-control/approval_queue.md`
- `mgf-control/approval_request.md`
- `mgf-control/session_checkpoint.md`
- `mgf-control/night_run_summary.md`
Scope respected: yes
Next recommended action: ejecutar QA técnica breve de `EL_Mogalef_Trend_Filter_V2` con `sa-qa`.
