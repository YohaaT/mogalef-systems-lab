PHASE: control
OBJECTIVE: Crear seguimiento persistente de uso de tokens para `mogalef-systems-lab`.
SCOPE: Solo artefactos de tracking. Sin abrir unidad técnica del lab.
INPUTS: `TOKEN_POLICY.md`, `RUN_PROTOCOL.md`, `mgf-control/phase_state.json`, snapshot actual de `session_status`.
EXPECTED ARTIFACT: `mgf-control/token_usage_log.csv` y `mgf-control/token_usage_summary.md`.
STOP CONDITION: detenerse al dejar el sistema de tracking persistido.

## Propósito
Llevar una estadística acumulativa del consumo de tokens del proyecto por run o wake, en archivos propios del proyecto, sin depender solo del snapshot transitorio de `/status`.

## Archivos canónicos
- `mgf-control/token_usage_log.csv`
- `mgf-control/token_usage_summary.md`

## Qué registrar al cierre de cada run
- `timestamp_utc`
- `session_key`
- `run_kind` (manual, cron, heartbeat, bootstrap, etc.)
- `phase`
- `objective`
- `component`
- `unit_type` (`build`, `fix`, `qa`, `re-qa`, `smoke`, `admin`, etc.)
- `tokens_in`
- `tokens_out`
- `cache_hit_percent`
- `context_tokens`
- `model`
- `result`
- `notes`

## Regla operativa
Al cierre de cada run relevante:
1. consultar snapshot de `session_status` si está disponible;
2. añadir una fila nueva a `token_usage_log.csv`;
3. actualizar este resumen si cambia la política o la lectura operativa.

## Limitación importante
OpenClaw `/status` da un snapshot de sesión actual, no un desglose exacto histórico por run.
Por tanto:
- este tracking será útil para estadística operativa;
- pero no garantiza precisión contable perfecta por wake pasado si no se registra en el momento de cierre.

## Baseline inicial registrado
- timestamp: `2026-04-15 12:35 UTC`
- tokens_in: `1.0k`
- tokens_out: `77`
- cache_hit_percent: `99`
- context_tokens: `73k`
- model: `openai-codex/gpt-5.4`

## Uso esperado
Este sistema permitirá revisar:
- consumo por componente
- consumo por fase
- consumo por tipo de unidad
- tendencia diaria o semanal
- wakes caros o poco eficientes

Result:
Artifacts created:
- `mgf-control/token_usage_log.csv`
- `mgf-control/token_usage_summary.md`
Files read:
- `TOKEN_POLICY.md`
- `RUN_PROTOCOL.md`
- `mgf-control/phase_state.json`
- snapshot actual de `session_status`
Scope respected: yes
Next recommended action: añadir una fila nueva al cierre de cada run o wake relevante.
