# Session checkpoint

## 2026-04-14 07:12 UTC
- Reanudación de Fase 1 detectada desde el punto posterior a `EL_MOGALEF_Bands`, que ya tenía spec y ambigüedades cerradas.
- Verificación previa: es prudente completar `EL_Stop_Intelligent` entero en este run. Fuente principal de 188 líneas, variante live y target usados solo como contraste semántico.
- Componente en curso: `EL_Stop_Intelligent`.

## 2026-04-14 07:20 UTC
- Componente completado: `EL_Stop_Intelligent`.
- Artefactos creados:
  - `mgf-stop-lab/spec/EL_Stop_Intelligent.md`
  - `mgf-stop-lab/notes/EL_Stop_Intelligent_ambiguities.md`
- Siguiente verificación previa: `EL_Mogalef_Trend_Filter_V2` es prudente de cerrar en este run. El fuente principal es acotado y su diferencia frente a V1 está localizada en la fórmula del repulse.

## 2026-04-14 07:31 UTC
- Componente completado: `EL_Mogalef_Trend_Filter_V2`.
- Artefactos creados:
  - `mgf-regime-filter-lab/spec/EL_Mogalef_Trend_Filter_V2.md`
  - `mgf-regime-filter-lab/notes/EL_Mogalef_Trend_Filter_V2_ambiguities.md`
- Siguiente verificación previa: `EL_NeutralZone_B_V2` es prudente de cerrar en este run. Fuente compacta y diferencia frente a la base suficientemente localizada.

## 2026-04-14 07:39 UTC
- Componente completado: `EL_NeutralZone_B_V2`.
- Artefactos creados:
  - `mgf-regime-filter-lab/spec/EL_NeutralZone_B_V2.md`
  - `mgf-regime-filter-lab/notes/EL_NeutralZone_B_V2_ambiguities.md`
- Límite prudente alcanzado para este run: 3 componentes cerrados completos, sin abrir Fase 2.
- Siguiente componente recomendado para otro run de Fase 1: `EL_STPMT_DIV`.

## 2026-04-14 07:56 UTC
- Nuevo run de Fase 1 iniciado con alcance explícito sobre los dos p0_core pendientes de divergencias.
- Componente completado: `EL_STPMT_DIV`.
- Artefactos creados:
  - `mgf-divergence-lab/spec/EL_STPMT_DIV.md`
  - `mgf-divergence-lab/notes/EL_STPMT_DIV_ambiguities.md`
- Componente completado: `EL_REPULSE_DIV`.
- Artefactos creados:
  - `mgf-divergence-lab/spec/EL_REPULSE_DIV.md`
  - `mgf-divergence-lab/notes/EL_REPULSE_DIV_ambiguities.md`
- Fase 1 p0_core queda cerrada para todos los componentes prioritarios definidos en `PROJECT_MASTER.md`.
- El run se detiene limpiamente aquí, sin abrir Fase 2, sin QA y sin backtest.

## 2026-04-14 08:26 UTC
- Run puntual de limpieza documental ejecutado únicamente sobre las specs p0_core marcadas como `FIX` en `mgf-control/spec_qa_report_p0.md`.
- Specs corregidas para dejarlas alineadas con el estándar de `EL_MOGALEF_Bands`:
  - `mgf-stop-lab/spec/EL_Stop_Intelligent.md`
  - `mgf-regime-filter-lab/spec/EL_Mogalef_Trend_Filter_V2.md`
  - `mgf-regime-filter-lab/spec/EL_NeutralZone_B_V2.md`
  - `mgf-divergence-lab/spec/EL_STPMT_DIV.md`
  - `mgf-divergence-lab/spec/EL_REPULSE_DIV.md`
- Ajustes aplicados solo a nivel documental:
  - eliminación de metadata de run incrustada
  - separación explícita entre núcleo funcional y visualización / alertas / accesorios
  - nota crítica de traducción sobre indexing retrospectivo y riesgo de lookahead
  - pseudocódigo mejorado o marcado explícitamente como estructural donde corresponde
  - referencia formal a los archivos de ambigüedades
- No se abrió Fase 2.
- No se hizo reconstrucción Python.
- No se hizo QA adicional.
- No se hizo backtest.
- El run se detiene aquí tras actualizar checkpoint y resumen.

## 2026-04-14 08:50 UTC
- Aprobación explícita recibida para abrir Fase 2 en un solo componente.
- Componente reconstruido: `EL_MOGALEF_Bands`.
- Artefactos creados:
  - `mgf-bands-lab/src/EL_MOGALEF_Bands.py`
  - `mgf-bands-lab/tests/EL_MOGALEF_Bands_test.py`
  - `mgf-bands-lab/notes/rebuild_EL_MOGALEF_Bands.md`
- La reconstrucción se hizo usando como definición funcional principal la spec canónica y como contraste el fuente original `mgf-bands-lab/base/EL_MOGALEF_Bands.txt`.
- Se documentaron decisiones de traducción sobre indexing cronológico, pasada retrospectiva, redondeo, desviación estándar y tratamiento del borde derecho.
- No se abrió Fase 3.
- No se hizo QA adicional.
- No se hizo backtest.
- No se tocaron otros componentes.
- El run se detiene aquí tras actualizar checkpoint y resumen.

## 2026-04-14 09:04 UTC
- QA técnica breve ejecutada únicamente sobre `EL_MOGALEF_Bands`.
- Archivos revisados:
  - `mgf-bands-lab/src/EL_MOGALEF_Bands.py`
  - `mgf-bands-lab/tests/EL_MOGALEF_Bands_test.py`
  - `mgf-bands-lab/notes/rebuild_EL_MOGALEF_Bands.md`
  - `mgf-bands-lab/spec/EL_MOGALEF_Bands.md`
- Artefacto creado:
  - `mgf-bands-lab/notes/qa_EL_MOGALEF_Bands.md`
- Dictamen del componente: `FIX`.
- Hallazgo técnico claro: el test actual usa un import inválido con guiones en el nombre del paquete, por lo que no es ejecutable tal como está.
- Hallazgo adicional: la lógica principal del rebuild es razonable, pero faltan tests mínimos sobre desplazamiento/no desplazamiento, stops y borde derecho de la pasada retrospectiva.
- No se modificó el código en este run.
- No se abrió Fase 3.
- No se hizo backtest.
- El run se detiene aquí tras guardar el reporte.

## 2026-04-14 11:50 UTC
- QA técnica breve ejecutada únicamente sobre `EL_Mogalef_Trend_Filter_V2` tras aprobación del usuario.
- Acciones ejecutadas:
  - ejecución de los tests locales `mgf-regime-filter-lab/tests/EL_Mogalef_Trend_Filter_V2_test.py` -> `ok`;
  - generación de artefactos de salida en `mgf-regime-filter-lab/outputs/smoke_test_EL_Mogalef_Trend_Filter_V2/` (cases + summary.json);
  - nota de QA persistida en `mgf-regime-filter-lab/notes/qa_EL_Mogalef_Trend_Filter_V2.md`.
- Resultados:
  - re-QA: PASS
  - smoke test automático: PASS
- Sincronización aplicada:
  - `phase_state.json` actualizado (componente marcado `PASS` en Fase 2 y Fase 3);
  - `mgf-control/approval_request.md` actualizado como procesado;
  - `mgf-control/approval_queue.md` verificada sin aprobaciones abiertas.
- Artefactos creados:
  - `mgf-regime-filter-lab/notes/qa_EL_Mogalef_Trend_Filter_V2.md`
  - `mgf-regime-filter-lab/outputs/smoke_test_EL_Mogalef_Trend_Filter_V2/`
  - `mgf-control/phase_state.json`
  - `mgf-control/session_checkpoint.md`
  - `mgf-control/night_run_summary.md`
- No se abrió `Fase 4`.
- No se hizo backtest.
- Próxima unidad válida preparada: `Fase 2` para `EL_NeutralZone_B_V2`.

Result:
Artifacts created:
- `mgf-regime-filter-lab/notes/qa_EL_Mogalef_Trend_Filter_V2.md`
- `mgf-regime-filter-lab/outputs/smoke_test_EL_Mogalef_Trend_Filter_V2/`
- `mgf-control/phase_state.json`
- `mgf-control/session_checkpoint.md`
- `mgf-control/night_run_summary.md`
Files read:
- `mgf-regime-filter-lab/spec/EL_Mogalef_Trend_Filter_V2.md`
- `mgf-regime-filter-lab/trend-overlays/EL_Mogalef_Trend_Filter_V2.txt`
- `mgf-regime-filter-lab/src/EL_Mogalef_Trend_Filter_V2.py`
- `mgf-regime-filter-lab/tests/EL_Mogalef_Trend_Filter_V2_test.py`
Scope respected: yes
Next recommended action: `Fase 2` para `EL_NeutralZone_B_V2`.

## 2026-04-14 21:08 UTC
- Componente completado: `EL_NeutralZone_B_V2`.
- Artefactos creados:
  - `mgf-regime-filter-lab/spec/EL_NeutralZone_B_V2.md`
  - `mgf-regime-filter-lab/notes/EL_NeutralZone_B_V2_ambiguities.md`
- Siguiente acción: no hay unidades inmediatas pendientes en Fase 2.

## 2026-04-15 08:07 UTC
- Revisión administrativa completa del estado del proyecto antes de recrear cron autónomo.
- Archivos inspeccionados:
  - `mgf-control/phase_state.json`
  - `mgf-control/approval_request.md`
  - `mgf-control/approval_queue.md`
  - `mgf-control/session_checkpoint.md`
  - `mgf-control/night_run_summary.md`
  - `mgf-control/workflow_operating_mode.md`
  - `/home/ubuntu/.openclaw/openclaw.json`
- Hallazgo corregido:
  - `EL_NeutralZone_B_V2` estaba en `PASS` en Fase 2 pero no reflejado todavía en Fase 3 dentro de `phase_state.json`.
  - `current_focus` también se dejó consistente con el estado real del proyecto.
- Estado tras la corrección:
  - sin aprobaciones abiertas;
  - sin cron activo previo;
  - siguiente unidad válida: preparar primera combinación mínima y esperar aprobación explícita antes de cualquier `Fase 4`.

## 2026-04-15 08:23 UTC
- Nuevo run iniciado por instrucción explícita del usuario con nueva prioridad:
  1. `EL_STPMT_DIV`
  2. `EL_REPULSE_DIV`
- Fuente de verdad usada en este arranque:
  - `PROJECT_MASTER.md`
  - `TOKEN_POLICY.md`
  - `RUN_PROTOCOL.md`
  - `mgf-control/phase_state.json`
  - `mgf-control/approval_queue.md`
  - `mgf-control/approval_request.md`
  - `mgf-control/session_checkpoint.md`
  - `mgf-control/night_run_summary.md`
  - `mgf-control/workflow_operating_mode.md`
  - spec, ambigüedades y fuente original de `EL_STPMT_DIV` y `EL_REPULSE_DIV`
- Componente completado en este bloque: `EL_STPMT_DIV`.
- Artefactos creados:
  - `mgf-divergence-lab/src/EL_STPMT_DIV.py`
  - `mgf-divergence-lab/tests/EL_STPMT_DIV_test.py`
  - `mgf-divergence-lab/notes/rebuild_EL_STPMT_DIV.md`
- Verificación local ejecutada:
  - `python3 mgf-divergence-lab/tests/EL_STPMT_DIV_test.py` -> `ok`
- QA técnica breve ejecutada después de la reconstrucción.
- Artefacto creado:
  - `mgf-divergence-lab/notes/qa_EL_STPMT_DIV.md`
- Dictamen del componente tras QA: `FIX`.
- Clasificación del ajuste requerido: `CODE_FIX` + `TEST_FIX`.
- Hallazgo principal: la semántica fina de pivots retrospectivos y la cobertura de tests de divergencia todavía no permiten promoverlo a `PASS`.
- No se abrió smoke formal.
- Siguiente acción disciplinada: fix de `EL_STPMT_DIV`, luego re-QA.

## 2026-04-15 09:01 UTC
- Run autónomo limitado a archivos de estado del proyecto.
- Inconsistencia administrativa detectada y corregida:
  - `phase_state.json` seguía apuntando a combinación mínima / espera de aprobación, pero el estado más reciente persistido en checkpoint y resumen ya dejaba `EL_STPMT_DIV` en `FIX` pendiente de corrección.
- Sin aprobación abierta y sin gate nuevo, pero no era válido avanzar a combinación mínima con `EL_STPMT_DIV` todavía en `FIX`.
- Artefacto actualizado:
  - `mgf-control/phase_state.json`
- Estado operativo correcto tras la sincronización:
  - componente actual: `EL_STPMT_DIV`
  - estado: `phase_2_fix_pending_after_qa_fix_dictamen`
  - siguiente unidad válida: un único run de fix de Fase 2 sobre `EL_STPMT_DIV`, seguido de re-QA en otro run.
- El run se detiene aquí tras persistir la corrección de estado.

## 2026-04-15 09:29 UTC
- Ejecutada la siguiente unidad técnica válida: fix único de Fase 2 sobre `EL_STPMT_DIV`.
- Corrección principal aplicada en código:
  - `temp1[$SmoothH]` y `temp4[$SmoothB]` ya no usan un desplazamiento doble en la confirmación retrospectiva de pivots; la traducción queda alineada con el offset de serie esperado por el host.
- Refuerzo de tests:
  - se añadieron casos dirigidos para `smooth=1` con divergencia bajista normal y alcista normal;
  - se validó también la propagación a `pose` y `sentiment`.
- Verificación local ejecutada:
  - `python3 mgf-divergence-lab/tests/EL_STPMT_DIV_test.py` -> `ok`
- Artefactos actualizados:
  - `mgf-divergence-lab/src/EL_STPMT_DIV.py`
  - `mgf-divergence-lab/tests/EL_STPMT_DIV_test.py`
  - `mgf-divergence-lab/notes/rebuild_EL_STPMT_DIV.md`
  - `mgf-control/phase_state.json`
  - `mgf-control/session_checkpoint.md`
  - `mgf-control/night_run_summary.md`
- No se ejecutó re-QA en este run, por disciplina de fase.
- Siguiente acción válida: `re-QA` de `EL_STPMT_DIV`.

## 2026-04-15 10:01 UTC
- Ejecutada la siguiente unidad técnica válida: `re-QA` de `EL_STPMT_DIV`.
- Verificaciones ejecutadas:
  - `python3 mgf-divergence-lab/tests/EL_STPMT_DIV_test.py` -> `ok`
  - comprobación dirigida adicional sobre las dos series sintéticas críticas ya incorporadas en tests para validar divergencia bajista normal y alcista normal con `smooth=1`, más propagación a `pose` y `sentiment`.
- Dictamen actualizado del componente: `PASS`.
- Sincronización aplicada:
  - `phase_state.json` actualizado para marcar `EL_STPMT_DIV` en `PASS` en Fase 2 y autoautorizado para Fase 3 pendiente de smoke;
  - `current_focus` movido a `EL_REPULSE_DIV` como siguiente prioridad válida.
- Artefactos actualizados:
  - `mgf-divergence-lab/notes/qa_EL_STPMT_DIV.md`
  - `mgf-control/phase_state.json`
  - `mgf-control/session_checkpoint.md`
  - `mgf-control/night_run_summary.md`
- No se abrió smoke formal en este run.
- Siguiente acción válida: `Fase 2` para `EL_REPULSE_DIV`.

## 2026-04-15 11:01 UTC
- Ejecutada la siguiente unidad técnica válida: rebuild de `EL_REPULSE_DIV` en `Fase 2`.
- Artefactos creados:
  - `mgf-divergence-lab/src/EL_REPULSE_DIV.py`
  - `mgf-divergence-lab/tests/EL_REPULSE_DIV_test.py`
  - `mgf-divergence-lab/notes/rebuild_EL_REPULSE_DIV.md`
- Verificación local ejecutada:
  - `python3 mgf-divergence-lab/tests/EL_REPULSE_DIV_test.py` -> `ok`
- Decisiones de traducción persistidas:
  - EMA estándar forward para `ExpMovingAverage`;
  - port del indexing retrospectivo a eje cronológico normal con offsets explícitos;
  - preservación del caso especial `smooth=1` para confirmación de pivots.
- Sin QA formal en este run, por disciplina de fase.
- Sin smoke formal en este run.
- Sin aprobación nueva requerida.
- Siguiente acción válida: `QA` técnica breve de `EL_REPULSE_DIV`.

## 2026-04-15 12:01 UTC
- Ejecutada la siguiente unidad técnica válida: `QA` técnica breve de `EL_REPULSE_DIV`.
- Verificaciones ejecutadas:
  - `python3 mgf-divergence-lab/tests/EL_REPULSE_DIV_test.py` -> `ok`
  - revisión cruzada contra spec y fuente original para confirmar cálculo Repulse, pivots retrospectivos con caso especial `smooth=1` y orden secuencial de agregación a `Pose`.
  - comprobación dirigida adicional con `duree_signal=3`, sin errores y con divergencias efectivas observadas en horizonte medio.
- Dictamen actualizado del componente: `PASS`.
- Sincronización aplicada:
  - `phase_state.json` actualizado para marcar `EL_REPULSE_DIV` en `PASS` en Fase 2;
  - autoautorizado a Fase 3 pendiente de smoke;
  - `current_focus` movido a `EL_STPMT_DIV` como siguiente prioridad válida para smoke.
- Artefactos actualizados:
  - `mgf-divergence-lab/notes/qa_EL_REPULSE_DIV.md`
  - `mgf-control/phase_state.json`
  - `mgf-control/session_checkpoint.md`
  - `mgf-control/night_run_summary.md`
- No se abrió `Fase 4`.
- No se hizo backtest.
- Siguiente acción válida: smoke de `EL_STPMT_DIV`.

## 2026-04-15 13:01 UTC
- Ejecutada la siguiente unidad técnica válida: smoke de `EL_STPMT_DIV` en `Fase 3`.
- Artefactos creados:
  - `mgf-divergence-lab/outputs/smoke_test_EL_STPMT_DIV/case_warmup_generic.json`
  - `mgf-divergence-lab/outputs/smoke_test_EL_STPMT_DIV/case_bearish_normal_smooth1.json`
  - `mgf-divergence-lab/outputs/smoke_test_EL_STPMT_DIV/case_bullish_normal_smooth1.json`
  - `mgf-divergence-lab/outputs/smoke_test_EL_STPMT_DIV/summary.json`
- Verificaciones ejecutadas:
  - warmup genérico con `compute_el_stpmt_div` para confirmar cola válida de `INDIC` sin `NaN` ni error estructural;
  - caso sintético de divergencia bajista normal con `smooth=1` -> `PASS`;
  - caso sintético de divergencia alcista normal con `smooth=1` -> `PASS`.
- Dictamen del smoke: `PASS`.
- Sincronización aplicada:
  - `phase_state.json` actualizado para marcar `EL_STPMT_DIV` en `PASS` también en `Fase 3`;
  - `current_focus` movido a `EL_REPULSE_DIV` como siguiente prioridad válida para smoke.
- No se abrió `Fase 4`.
- No se hizo backtest.
- Siguiente acción válida: smoke de `EL_REPULSE_DIV`.

## 2026-04-15 14:01 UTC
- Ejecutada la siguiente unidad técnica válida: smoke de `EL_REPULSE_DIV` en `Fase 3`.
- Artefactos creados:
  - `mgf-divergence-lab/outputs/smoke_test_EL_REPULSE_DIV/case_warmup_generic.json`
  - `mgf-divergence-lab/outputs/smoke_test_EL_REPULSE_DIV/case_bearish_short_horizon.json`
  - `mgf-divergence-lab/outputs/smoke_test_EL_REPULSE_DIV/case_bullish_short_horizon.json`
  - `mgf-divergence-lab/outputs/smoke_test_EL_REPULSE_DIV/summary.json`
- Verificaciones ejecutadas:
  - warmup genérico con `compute_el_repulse_div` para confirmar cola válida de `INDICM` sin `NaN` ni error estructural;
  - caso observado `case_bearish_short_horizon` en índice 77 -> `DIVBM=-0.4`, `Pose=-1`, `sentiment=0`;
  - caso observado `case_bullish_short_horizon` en índice 153 -> `DIVHM=0.4`, `Pose=1`, `sentiment=100`.
- Dictamen del smoke: `PASS`.
- Sincronización aplicada:
  - `phase_state.json` actualizado para marcar `EL_REPULSE_DIV` en `PASS` también en `Fase 3`;
  - conjunto prioritario actual queda completo en `Fase 3`.
- No se abrió `Fase 4`.
- No se hizo backtest.
- Siguiente acción válida: esperar aprobación explícita antes de cualquier trabajo de `Fase 4`.

## 2026-04-15 17:12 UTC
- Nueva unidad autorizada por el usuario: preparar la primera estrategia mínima combinada para futuro backtest, sin abrir `Fase 4`.
- Base obligatoria usada para la propuesta:
  - `EL_MOGALEF_Bands`
  - `EL_Mogalef_Trend_Filter_V2`
  - `EL_Stop_Intelligent`
  - evaluación comparativa de entrada entre `EL_STPMT_DIV` y `EL_REPULSE_DIV`
- Artefacto creado:
  - `mgf-control/first_minimal_strategy_candidate.md`
- Decisión recomendada en la propuesta:
  - primera variante de entrada: `EL_STPMT_DIV`
  - variante inmediata posterior y separada: `EL_REPULSE_DIV`
- Gate preparado sin abrir `Fase 4`:
  - `mgf-control/approval_request.md` actualizado a `waiting_user_approval`
  - `phase_state.json` actualizado para reflejar candidato preparado y espera de aprobación explícita
- No se abrió backtest.
- No se abrió `Fase 4` en este run.
- Siguiente acción válida: esperar decisión explícita del usuario sobre apertura de `Fase 4` para la combinación mínima propuesta.

## 2026-04-15 18:01 UTC
- Run autónomo limitado a archivos de estado del proyecto.
- Inconsistencia administrativa real detectada y corregida:
  - `approval_request.md` y `phase_state.json` indicaban `waiting_user_approval`, pero `approval_queue.md` seguía marcando cola vacía.
- Sincronización aplicada:
  - `approval_queue.md` actualizado para reflejar la solicitud abierta `phase_4_open_first_minimal_combined_strategy_candidate`.
- Reevaluación inmediata posterior:
  - sigue existiendo un gate real `Fase 3 -> Fase 4`;
  - `awaiting_user_approval = true`;
  - no hay unidad técnica válida ejecutable en Fases 2 o 3 sin abrir indebidamente `Fase 4`.
- El run se detiene aquí tras persistir estado coherente.
- Notificación pendiente: Telegram al usuario indicando que el proyecto sigue esperando aprobación explícita para abrir `Fase 4`.

## 2026-04-15 18:31 UTC
- Aprobación explícita recibida para abrir únicamente `phase_4_open_first_minimal_combined_strategy_candidate`.
- Se intentó ejecutar `Fase 4` sobre la estrategia mínima combinada aprobada:
  - `EL_MOGALEF_Bands`
  - `EL_Mogalef_Trend_Filter_V2`
  - `EL_Stop_Intelligent`
  - entrada: `EL_STPMT_DIV`
- Bloqueo real detectado durante el run:
  - no existe dataset OHLC persistido y verificable en el workspace para ejecutar un backtest serio y reproducible;
  - tampoco queda fijado en disco el universo y marco temporal concretos de la primera corrida.
- Artefactos creados:
  - `mgf-control/backtest_first_minimal_strategy.md`
  - `mgf-control/backtest_first_minimal_strategy_summary.md`
- Sincronización aplicada:
  - `phase_state.json` actualizado a estado de bloqueo real de `Fase 4` por falta de dataset/universo/timeframe;
  - `awaiting_user_approval` cerrado porque la aprobación ya fue consumida;
  - no se abrió trabajo sobre otras estrategias ni otros componentes.
- Dictamen del intento de backtest: `BLOCK`.
- Siguiente acción válida: esperar dataset local verificable y definición explícita de universo y marco temporal para rerun de esta misma estrategia mínima.

## 2026-04-15 18:43 UTC
- Nueva unidad autorizada por el usuario: preparar la especificación de datos para habilitar backtests reproducibles, sin abrir `Fase 4`.
- Artefactos creados:
  - `mgf-control/market_data_requirements.md`
  - `mgf-control/market_data_acquisition_plan.md`
- La especificación dejó definidos:
  - universo inicial recomendado: un solo símbolo líquido;
  - marco temporal inicial recomendado: `15m`;
  - sesión/horario: sesión principal del instrumento, barras fuera de sesión excluidas, timestamps en UTC;
  - columnas mínimas del dataset: `timestamp_utc`, `symbol`, `open`, `high`, `low`, `close`, `volume`;
  - almacenamiento local recomendado: CSV canónico en `mgf-data/market/`;
  - convención de nombres de archivo;
  - criterios mínimos de calidad y validación del dataset;
  - lista exacta de lo que falta para desbloquear el rerun de `Fase 4`.
- No se descargaron datos.
- No se abrió backtest.
- `phase_state.json` actualizado para reflejar que la capa de datos queda especificada y ahora se espera selección explícita de símbolo y autorización de adquisición/carga local.
- Siguiente acción válida: esperar símbolo inicial explícito y autorización para adquirir o cargar datos locales.

## 2026-04-15 18:47 UTC
- Nueva unidad autorizada por el usuario: preparar la unidad de adquisición de datos para habilitar backtests reproducibles, sin abrir `Fase 4`.
- Artefactos creados:
  - `mgf-control/market_data_source_decision.md`
  - `mgf-control/market_data_download_unit.md`
  - `mgf-control/market_data_validation_checklist.md`
  - `mgf-control/approval_request.md`
- Decisiones persistidas en esta unidad:
  - fuente propuesta: archivo OHLCV local aportado o autorizado por el usuario;
  - instrumento inicial exacto: `SPY`;
  - timeframe inicial exacto: `15m`;
  - rango temporal inicial sugerido: `2023-01-01` a `2024-12-31`;
  - formato local: CSV canónico;
  - ruta esperada: `mgf-data/market/SPY__15m__regular_session__2023-01-01__2024-12-31.csv`.
- La descarga o carga real no se ejecutó porque todavía falta autorización explícita.
- Gate preparado:
  - `approval_request.md` abierto con `market_data_acquisition_for_SPY_15m_2023_2024`.
- `phase_state.json` actualizado para reflejar que la unidad de adquisición está preparada y espera aprobación explícita.
- No se abrió backtest.
- No se abrió `Fase 4`.
- Siguiente acción válida: esperar aprobación explícita para cargar archivo local o descargar datos del dataset definido.

## 2026-04-15 19:40 UTC
- El usuario rechazó explícitamente `market_data_acquisition_for_SPY_15m_2023_2024`.
- Motivo persistido: `SPY` no es coherente con el objetivo del proyecto, que está orientado a futuros y ejecución posterior en NinjaTrader 8.
- Corrección aplicada únicamente sobre la capa de datos, sin abrir `Fase 4` y sin descargar datos.
- Propuesta reemplazada por una alineada con futuros:
  - instrumento inicial exacto: `MNQ`;
  - timeframe inicial exacto: `10m`;
  - rango temporal inicial: `2023-01-01` a `2024-12-31`;
  - formato local: CSV canónico;
  - ruta esperada: `mgf-data/market/MNQ__10m__regular_session__2023-01-01__2024-12-31.csv`.
- Gate sustituido y preparado:
  - nueva solicitud abierta: `market_data_acquisition_for_MNQ_10m_2023_2024`.
- `approval_request.md`, `approval_queue.md` y `phase_state.json` sincronizados con la nueva propuesta.
- No se abrió backtest.
- No se abrió `Fase 4`.
- Siguiente acción válida: esperar aprobación explícita para cargar archivo local o descargar datos del dataset `MNQ 10m` definido.

## 2026-04-15 19:46 UTC
- El usuario rechazó todavía el gate actual para forzar una base única, simple y estable para el primer dataset.
- Corrección aplicada únicamente sobre la propuesta de datos, sin descargar datos y sin abrir `Fase 4`.
- Base final persistida para el primer dataset reproducible:
  - instrumento inicial exacto: `MNQ`;
  - timeframe inicial exacto: `10m`;
  - rango temporal inicial: `2023-01-01` a `2024-12-31`;
  - formato: `CSV`;
  - gate previo a adquisición real: mantenido.
- Se eliminaron de la propuesta referencias a alternativas adicionales de timeframe.
- Gate corregido y mantenido:
  - `market_data_acquisition_for_MNQ_10m_2023_2024`.
- `approval_request.md`, `approval_queue.md` y `phase_state.json` quedaron sincronizados.
- No se abrió backtest.
- No se abrió `Fase 4`.
- Siguiente acción válida: esperar aprobación explícita para carga local o descarga real del dataset `MNQ 10m` definido.

## 2026-04-15 19:49 UTC
- El usuario concedió aprobación explícita para ejecutar únicamente `market_data_acquisition_for_MNQ_10m_2023_2024`.
- Se intentó primero respetar la vía local reproducible buscando datasets `MNQ` ya presentes en el workspace.
- Hallazgos relevantes localizados:
  - `workspace/collab/Working/tank/datasets_raw/MNQ/contracts/MNQH26.CME.csv`
  - `workspace/collab/Working/tank/datasets_raw/MNQ/contracts/MNQH27.CME.csv`
  - `workspace/collab/Working/tank/datasets_raw/MNQ/contracts/MNQM26.CME.csv`
  - `workspace/collab/Working/tank/datasets_raw/MNQ/contracts/MNQU26.CME.csv`
  - `workspace/collab/Working/tank/datasets_raw/MNQ/contracts/MNQZ26.CME.csv`
- Resultado del intento: `FAIL_BLOCK`.
- Motivos reales del fallo:
  - los archivos localizados no cubren de forma suficiente el rango `2023-01-01` a `2024-12-31`;
  - la granularidad observada no está alineada claramente con `10m`;
  - no existe material local suficiente para construir honestamente el CSV objetivo sin cambiar alcance.
- Decisión aplicada:
  - no se creó `mgf-data/market/MNQ__10m__regular_session__2023-01-01__2024-12-31.csv`;
  - se creó `mgf-control/market_data_validation_report.md` con dictamen `FAIL_BLOCK`.
- `phase_state.json` actualizado para reflejar fallo de adquisición por falta de dataset local apto.
- No se abrió backtest.
- No se abrió `Fase 4`.
- No se dejó gate para reabrir `Fase 4` porque el prerequisito de datos no quedó satisfecho.
- Siguiente acción válida: aportar un archivo local correcto para `MNQ 10m 2023-01-01 -> 2024-12-31` o autorizar una descarga externa concreta de ese dataset exacto.

## 2026-04-15 20:05 UTC
- Cambio de prioridad autorizado por el usuario: omitir por ahora el requisito de dataset nativo en `10m`.
- Nueva unidad ejecutada: adquirir, guardar, normalizar y validar un dataset reproducible de `MNQ 5m` como base práctica de trabajo.
- Fuente viable usada en este entorno:
  - `Yahoo Finance chart API`
  - símbolo en origen: `MNQ=F`
  - rango efectivo accesible: ventana intradía reciente limitada por fuente
  - parámetro usado: `range=60d`, `interval=5m`
- Artefacto CSV creado:
  - `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`
- Cobertura real obtenida:
  - primer timestamp útil: `2026-02-03T05:05:00Z`
  - último timestamp útil: `2026-04-15T19:56:20Z`
  - filas válidas: `13725`
- Validación estructural: `PASS_WITH_SCOPE_LIMIT`.
- Limitación documentada explícitamente:
  - la fuente no entregó `2023-2024`;
  - el dataset representa una ventana reciente y práctica, no una validación histórica definitiva.
- Artefactos de control creados/actualizados:
  - `mgf-control/market_data_source_used.md`
  - `mgf-control/market_data_validation_report.md`
  - `mgf-control/market_data_scope_note.md`
  - `mgf-control/session_checkpoint.md`
  - `mgf-control/night_run_summary.md`
  - `mgf-control/phase_state.json`
- No se abrió backtest.
- No se abrió `Fase 4`.
- El dataset queda autorizado para pruebas, smoke tests, validación funcional y backtests ligeros, dentro del alcance documentado.
- Siguiente acción válida: usar esta base `MNQ 5m` en trabajo técnico autorizado, manteniendo la reserva sobre validación histórica definitiva.

## 2026-04-15 20:12 UTC
- El usuario autorizó abrir `Fase 4` únicamente sobre la `first minimal combined strategy candidate` usando solo el dataset práctico `MNQ 5m` ya validado.
- Backtest ligero ejecutado sobre:
  - dataset: `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`
  - estrategia: `EL_MOGALEF_Bands` + `EL_Mogalef_Trend_Filter_V2` + `EL_STPMT_DIV` + `EL_Stop_Intelligent`
- Reglas usadas en el run:
  - filtro `Trend Filter V2 = pass`
  - entrada por `STPMT_DIV pose = 1/-1`
  - contexto `close` dentro de `MOGALEF Bands`
  - salida por `Stop Intelligent`
  - una sola posición a la vez
- Métricas observadas:
  - trades: `116`
  - win rate: `93.97%`
  - net points: `152920.6`
  - profit factor: `90.5176`
- Dictamen persistido: `FIX`.
- Motivo del `FIX`:
  - métricas demasiado buenas para ser creíbles;
  - sospecha real de sesgo temporal/lookahead en la integración actual barra a barra;
  - el run sirve como validación funcional ligera de integración, no como lectura fiable del edge.
- Artefactos creados:
  - `mgf-control/backtest_first_minimal_strategy.md`
  - `mgf-control/backtest_first_minimal_strategy_summary.md`
  - `mgf-control/backtest_first_minimal_strategy_scope_note.md`
- `phase_state.json` actualizado para reflejar `Fase 4` ligera ejecutada con necesidad de fix metodológico antes de cualquier interpretación adicional.
- No se abrió `Fase 4` para otros sistemas.
- No se cambiaron arquitecturas.
- Siguiente acción válida: revisar y corregir la metodología temporal del backtest antes de rerun o interpretación más seria.

## 2026-04-15 20:35 UTC
- El usuario pidió auditar claramente qué hace la estrategia y dónde está la contaminación del backtest.
- Auditoría técnica ejecutada sobre la integración de componentes en el dataset práctico `MNQ 5m`.
- Explicación funcional persistida:
  - la estrategia usa `STPMT_DIV` como disparo de entrada;
  - `Trend Filter V2` como permiso/bloqueo de régimen;
  - `MOGALEF Bands` como filtro de contexto estructural;
  - `Stop Intelligent` como salida dinámica.
- Hallazgo principal persistido:
  - el problema más serio no parece ser solo la entrada en `t+1`;
  - `EL_MOGALEF_Bands` y `EL_Stop_Intelligent` están contaminando el backtest al usarse como si fueran motores causales de estrategia cuando su forma actual es retrospectiva/indicador.
- Evidencia resumida:
  - `Bands` muestra canales plenamente definidos y muy estables desde barras tempranas;
  - `Stop Intelligent` produce stops long/short no nulos desde el índice `0` cuando se le da una trayectoria simplificada de posición.
- Dictamen de auditoría:
  - principal componente problemático: `EL_Stop_Intelligent`;
  - segundo componente problemático: `EL_MOGALEF_Bands`;
  - `Trend Filter V2` parece menos sospechoso en esta pasada;
  - `STPMT_DIV` queda pendiente de revisión causal fina.
- Artefacto creado:
  - `mgf-control/backtest_component_audit.md`
- Siguiente acción válida: diseñar wrappers causales de `Bands` y `Stop Intelligent` antes de cualquier rerun serio.

## 2026-04-15 20:43 UTC
- El usuario autorizó avanzar con el diseño del wrapper causal y pidió recoger adicionalmente día y hora de ejecuciones y cierres para estudiar horarios de efectividad.
- Artefacto creado:
  - `mgf-control/backtest_causal_wrapper_design.md`
- Decisión persistida:
  - todo rerun serio futuro debe registrar por trade el timestamp de señal, entrada y salida;
  - además debe guardar `entry_day_of_week`, `entry_hour_utc`, `exit_day_of_week`, `exit_hour_utc`, razón de salida y duración en barras.
- Objetivo explícito de ese registro:
  - detectar mejores horarios y franjas con mayor efectividad.
- El diseño deja claro que el wrapper causal debe separar:
  - señal en barra `t`;
  - ejecución en `t+1`;
  - gestión de stop solo con información disponible hasta la barra actual.
- Siguiente acción válida: implementar el wrapper causal y generar trade log explotable para análisis por día/hora.

## 2026-04-15 20:44 UTC
- El usuario autorizó ejecutar el siguiente paso completo.
- Wrapper causal ligero implementado y corrido sobre `MNQ 5m`.
- En este rerun se usó un motor causal simplificado con:
  - `EL_STPMT_DIV` como disparo;
  - `EL_Mogalef_Trend_Filter_V2` como filtro de permiso;
  - stop causal simple basado en la barra de señal;
  - salida por stop o por señal opuesta.
- `EL_MOGALEF_Bands` y `EL_Stop_Intelligent` quedaron fuera del motor de ejecución de este rerun por la contaminación detectada en auditoría.
- Artefactos creados:
  - `mgf-control/backtest_first_minimal_strategy_causal.md`
  - `mgf-control/backtest_first_minimal_strategy_trade_log.csv`
- Resultado principal del rerun causal:
  - trades: `97`
  - wins: `17`
  - losses: `80`
  - net points: `1369.5`
- Se incorporó el registro horario pedido por el usuario:
  - `entry_day_of_week`
  - `entry_hour_utc`
  - `exit_day_of_week`
  - `exit_hour_utc`
  - `exit_reason`
  - `bars_in_trade`
- Primeras franjas observadas con mejor neto en esta muestra:
  - horas `13`, `14`, `21`, `18`, `22` UTC
  - días `Thursday`, `Wednesday`, `Friday`, `Tuesday`
- Siguiente acción válida: explotar el trade log para ranking horario más fino o reintroducir wrappers causales más sofisticados de `Bands` y `Stop Intelligent`.

## 2026-04-15 20:53 UTC
- El usuario pidió añadir `R:R` al backtest y ejecutar la reintroducción sugerida.
- `R:R` incorporado al trade log causal.
- Nuevo artefacto generado:
  - `mgf-control/backtest_first_minimal_strategy_trade_log_rr.csv`
- Métricas `R:R` observadas:
  - `R:R` medio: `1.3025`
  - `R:R` mediano: `-1.0`
  - mejor `R:R`: `47.81`
  - peor `R:R`: `-1.0`
- Reintroducción ejecutada:
  - `EL_MOGALEF_Bands` reintroducido de forma conservadora como filtro amplio con warmup.
- Resultado de la reintroducción:
  - no cambió las métricas del rerun causal (`97` trades, `1369.5` net points).
- Interpretación persistida:
  - `Bands` así reintroducido no aporta discriminación observable útil en esta muestra, o todavía no está listo para uso causal fino.
- Artefacto creado:
  - `mgf-control/backtest_rr_and_reintroduction_note.md`
- Siguiente acción válida: explotar el trade log con `R:R` y análisis horario, o diseñar una reintroducción causal estricta de `Stop Intelligent`.

## 2026-04-15 21:06 UTC
- El usuario cambió el objetivo operativo del proyecto.
- Nueva prioridad persistida:
  - explorar combinaciones de componentes de forma disciplinada;
  - usar métricas solo como guía comparativa débil;
  - no tratar resultados actuales como validación seria del sistema.
- Reglas persistidas:
  - etiquetar cada combinación como `provisional_usable_for_ranking`, `contaminated_by_noncausal_component` o `blocked_for_strategy_use`;
  - si usa `EL_MOGALEF_Bands` o `EL_Stop_Intelligent` en modo no causal, marcarla como `contaminated_by_noncausal_component`;
  - seguir avanzando salvo bloqueo técnico real, falta de datos, inconsistencia de integración o gate de fase real.
- Artefactos creados:
  - `mgf-control/combination_exploration_policy.md`
  - `mgf-control/combination_registry.md`
- Registro inicial persistido de combinaciones ya probadas:
  - `COMB_001`: `STPMT_DIV + Trend_Filter_V2 + stop causal simple` -> `provisional_usable_for_ranking`
  - `COMB_002`: `STPMT_DIV + Trend_Filter_V2 + Bands + Stop_Intelligent` -> `contaminated_by_noncausal_component`
  - `COMB_003`: `STPMT_DIV + Trend_Filter_V2 + Bands(reintroducción conservadora) + stop causal simple` -> `contaminated_by_noncausal_component`
- Próxima prioridad operativa: seguir con combinaciones usando `EL_STPMT_DIV` y `EL_REPULSE_DIV` contra `Trend_Filter_V2`, `NeutralZone_B_V2`, `Bands` y `Stop_Intelligent`, etiquetando correctamente cada caso.
- Siguiente acción válida: continuar exploración disciplinada de combinaciones y actualizar el registro.

## 2026-04-15 21:12 UTC
- El usuario autorizó ejecutar la siguiente tanda exploratoria.
- Resultado de la ronda:
  - `EL_NeutralZone_B_V2` bloquea dos combinaciones priorizadas por inconsistencia real: no existe rebuild Python usable en `src`.
  - `EL_REPULSE_DIV + EL_Mogalef_Trend_Filter_V2 + stop causal simple` sí pudo correrse.
- Métricas orientativas de `COMB_005`:
  - trades: `227`
  - wins: `35`
  - losses: `192`
  - net points: `49.5`
  - avg points: `0.2181`
- Lectura persistida:
  - `COMB_005` es usable para ranking provisional, pero en esta muestra queda claramente por detrás de `STPMT_DIV + Trend Filter V2 + stop causal simple`.
  - `COMB_004` y `COMB_006` quedan bloqueadas por falta de implementación usable de `NeutralZone_B_V2`.
- Artefactos creados/actualizados:
  - `mgf-control/combination_registry.md`
  - `mgf-control/combination_exploration_round_001.md`
- Siguiente acción válida: decidir si conviene reconstruir `EL_NeutralZone_B_V2` para desbloquear exploración adicional o seguir con otras combinaciones ya implementadas.

## 2026-04-15 21:22 UTC
- Backend ACP volvió a fallar con el mismo error `ACP runtime backend is currently unavailable`.
- Se activó la excepción temporal autorizada por el usuario para ejecutar esta unidad en BO manteniendo exactamente el mismo flujo disciplinado.
- `EL_NeutralZone_B_V2` quedó reconstruido y cerrado en `PASS`:
  - rebuild Fase 2 -> `PASS`
  - QA técnica -> `PASS`
  - smoke Fase 3 -> `PASS`
- Artefactos creados del componente:
  - `mgf-regime-filter-lab/src/EL_NeutralZone_B_V2.py`
  - `mgf-regime-filter-lab/tests/EL_NeutralZone_B_V2_test.py`
  - `mgf-regime-filter-lab/notes/rebuild_EL_NeutralZone_B_V2.md`
  - `mgf-regime-filter-lab/notes/qa_EL_NeutralZone_B_V2.md`
  - `mgf-regime-filter-lab/notes/smoke_EL_NeutralZone_B_V2.md`
- Rerun de combinaciones desbloqueadas realizado:
  - `COMB_004`: `STPMT_DIV + EL_NeutralZone_B_V2 + stop causal simple` -> `provisional_usable_for_ranking`
  - `COMB_006`: `REPULSE_DIV + EL_NeutralZone_B_V2 + stop causal simple` -> `provisional_usable_for_ranking`
- Métricas orientativas observadas:
  - `COMB_004`: trades `111`, net points `1326.5`
  - `COMB_006`: trades `261`, net points `-976.5`
- Lectura persistida:
  - la rama `STPMT_DIV + NeutralZone_B_V2` queda mejor posicionada para ranking provisional que la rama `REPULSE_DIV + NeutralZone_B_V2`.
- Artefactos creados/actualizados:
  - `mgf-control/neutralzone_rebuild_and_combos.md`
  - `mgf-control/combination_registry.md`
- No se abrió Fase 4 definitiva.
- No se presentó edge definitivo.
- Siguiente acción válida: continuar exploración disciplinada de combinaciones limpias/provisionales disponibles.

## 2026-04-15 21:33 UTC
- El usuario autorizó seguir con la siguiente ronda limpia/provisional.
- Ronda ejecutada:
  - `COMB_007`: `STPMT_DIV + Trend_Filter_V2 + NeutralZone_B_V2 + stop causal simple`
  - `COMB_008`: `REPULSE_DIV + Trend_Filter_V2 + NeutralZone_B_V2 + stop causal simple`
  - `COMB_009`: consenso `STPMT_DIV + REPULSE_DIV + Trend_Filter_V2 + stop causal simple`
- Resultado comparativo orientativo:
  - `COMB_007`: trades `64`, net points `357.75`
  - `COMB_008`: trades `167`, net points `-2014.0`
  - `COMB_009`: trades `15`, net points `-472.5`
- Lectura persistida:
  - `COMB_007` es la mejor de esta ronda para ranking provisional;
  - las ramas `REPULSE_DIV` siguen quedando por detrás en esta muestra;
  - la exigencia de consenso `STPMT + REPULSE` reduce demasiado la actividad y no mejora la lectura exploratoria actual.
- Artefactos creados/actualizados:
  - `mgf-control/combination_registry.md`
  - `mgf-control/combination_exploration_round_002.md`
- Siguiente acción válida: seguir profundizando primero en la familia `STPMT_DIV` antes de gastar más coste en ramas `REPULSE_DIV`.

## 2026-04-15 21:38 UTC
- El usuario autorizó profundizar la familia `STPMT_DIV`.
- Ronda ejecutada:
  - `COMB_010`: `STPMT_DIV + NeutralZone_B_V2(signal)`
  - `COMB_011`: `STPMT_DIV + (Trend_Filter_V2 OR NeutralZone_B_V2(filter))`
  - `COMB_012`: `STPMT_DIV + Trend_Filter_V2 + NeutralZone_B_V2(signal)`
- Resultado comparativo orientativo:
  - `COMB_010`: trades `3`, net points `-61.0`
  - `COMB_011`: trades `175`, net points `966.0`
  - `COMB_012`: trades `1`, net points `-12.5`
- Lectura persistida:
  - `COMB_011` es la rama más útil de esta ronda para ranking provisional;
  - `COMB_010` y `COMB_012` son demasiado restrictivas para esta muestra.
- Artefactos creados/actualizados:
  - `mgf-control/combination_registry.md`
  - `mgf-control/combination_exploration_round_003.md`
- Siguiente acción válida: consolidar ranking provisional de la familia `STPMT_DIV` y decidir si se quiere análisis horario por combinación o nueva tanda exploratoria.

## 2026-04-15 21:42 UTC
- Nueva directriz persistida:
  - congelar `REPULSE_DIV` como rama secundaria;
  - priorizar únicamente la rama `STPMT_DIV`;
  - no abrir más rondas libres fuera de STPMT sin autorización explícita;
  - volver a respetar estrictamente una unidad principal por run.
- Unidad ejecutada: comparación enfocada solo entre `COMB_001`, `COMB_004` y `COMB_007`.
- Artefacto creado:
  - `mgf-control/stpmt_branch_comparison.md`
- Dictamen comparativo provisional persistido:
  - mejor candidata provisional actual: `COMB_001`
  - segunda candidata provisional: `COMB_004`
  - tercera candidata provisional: `COMB_007`
- Motivo resumido:
  - `COMB_001` ofrece mejor equilibrio entre simplicidad estructural, actividad suficiente y menor coste de complejidad;
  - `COMB_004` queda cerca como alternativa simple y válida;
  - `COMB_007` añade doble filtro y más complejidad sin justificar prioridad superior en esta etapa.
- `phase_state.json` actualizado para reflejar selección provisional de rama STPMT.
- No se abrieron nuevas combinaciones fuera de las tres autorizadas.
- No se abrió Fase 4.
- No se presentó edge definitivo.
- Siguiente acción válida: desarrollar primero `COMB_001` y mantener `COMB_004` como rama secundaria viva dentro de STPMT.

## 2026-04-16 09:16 UTC
- Nueva prioridad principal persistida:
  - `COMB_001` pasa a ser la rama principal de desarrollo;
  - `COMB_004` queda como rama secundaria;
  - `COMB_007` queda depriorizada.
- Unidad ejecutada: preparación de la especificación operativa clara y reusable de `COMB_001`.
- Artefactos creados:
  - `mgf-control/strategy_candidate_COMB_001.md`
  - `mgf-control/strategy_candidate_COMB_001_rules.md`
- La documentación deja fijado:
  - componentes exactos usados;
  - rol de cada componente;
  - lógica mínima de entrada;
  - filtro/contexto;
  - salida/riesgo;
  - orden temporal de evaluación;
  - supuestos actuales;
  - límites y advertencias;
  - iteraciones lógicas siguientes sin abrir Fase 4 definitiva.
- `phase_state.json` actualizado para reflejar que `COMB_001` ya queda preparado como estrategia candidata principal a nivel operativo.
- No se abrieron nuevas combinaciones.
- No se abrió Fase 4.
- No se presentó edge definitivo.
- Siguiente acción válida: usar `COMB_001` como contrato operativo base de las próximas iteraciones sobre la rama principal.

## 2026-04-16 09:31 UTC
- La rama principal del proyecto queda fijada explícitamente en `COMB_001`.
- Unidad ejecutada: preparación de la hoja de ruta de iteración controlada de `COMB_001`.
- Artefactos creados:
  - `mgf-control/COMB_001_iteration_plan.md`
  - `mgf-control/COMB_001_next_change_candidates.md`
- El plan deja definido:
  - estado actual de `COMB_001`;
  - principales límites actuales;
  - 3 cambios mínimos candidatos;
  - coste/beneficio esperado de cada cambio;
  - recomendación explícita de probar primero el refinamiento de la salida causal simple (`Candidato A`);
  - por qué iterar sobre `COMB_001` es mejor que abrir nuevas combinaciones.
- `phase_state.json` actualizado para reflejar que el plan de iteración ya está preparado.
- No se ejecutó todavía la siguiente iteración.
- No se abrieron nuevas combinaciones.
- No se abrió Fase 4.
- No se presentó edge definitivo.
- Siguiente acción válida: si el usuario lo autoriza, ejecutar primero el `Candidato A` sobre `COMB_001`.

## 2026-04-16 09:34 UTC
- Nueva unidad autorizada: ejecutar `Candidato A` sobre `COMB_001` sin abrir nuevas combinaciones y sin Fase 4.
- Restricción respetada:
  - no se cambió la entrada;
  - no se cambió el filtro;
  - no se abrieron ramas paralelas.
- Cambio exacto aplicado a nivel de definición operativa:
  - refinamiento de la salida causal simple añadiendo break-even tras avance favorable de `1R`.
- Artefactos creados:
  - `mgf-control/COMB_001_candidate_A_impl.md`
  - `mgf-control/COMB_001_candidate_A_rules.md`
- La documentación deja claro:
  - qué cambio exacto se aplicó en la salida;
  - por qué;
  - cómo cambia la lógica respecto a `COMB_001` base;
  - qué queda pendiente para evaluar después.
- `phase_state.json` actualizado para reflejar que `Candidato A` queda preparado pero aún no evaluado.
- No se ejecutó backtest definitivo.
- No se abrieron nuevas combinaciones.
- No se abrió Fase 4.
- Siguiente acción válida: si se autoriza, evaluar `COMB_001 Candidate A` contra la versión base de `COMB_001`.

## 2026-04-16 09:36 UTC
- Nueva unidad autorizada: comparar `COMB_001` base frente a `COMB_001 Candidate A` usando exactamente el mismo dataset práctico.
- Restricciones respetadas:
  - no se abrieron nuevas combinaciones;
  - no se abrió Fase 4;
  - no se presentó edge definitivo.
- Resultado comparativo orientativo:
  - base: trades `97`, net points `1369.5`, avg points `14.1186`
  - Candidate A: trades `110`, net points `-116.25`, avg points `-1.0568`, flats `59`
- Lectura persistida:
  - `Candidate A` volvió demasiados trades a break-even y degradó el neto de la rama principal en esta muestra.
- Dictamen final persistido:
  - `keep_base`
- Artefactos creados:
  - `mgf-control/COMB_001_candidate_A_comparison.md`
  - `mgf-control/COMB_001_candidate_A_summary.md`
- `phase_state.json` actualizado para reflejar que `COMB_001` base sigue siendo la versión principal vigente.
- Siguiente acción válida: si se autoriza otra iteración, preparar un candidato distinto para `COMB_001`.

## 2026-04-16 09:41 UTC
- Resultado fijado de la unidad anterior persistido:
  - `COMB_001` base se mantiene frente a `Candidate A`
  - `Candidate A` queda descartado
  - dictamen formal: `keep_base`
- Nueva unidad autorizada: registrar ese descarte y preparar/ejecutar `Candidate B`, luego compararlo contra `COMB_001` base con el mismo dataset y mismo alcance ligero.
- `Candidate B` definido como:
  - restricción horaria mínima de entrada sobre `COMB_001`
  - horas permitidas: `13`, `14`, `18`, `21`, `22` UTC
- Comparación orientativa realizada con el mismo dataset práctico:
  - base: trades `97`, net points `1369.5`, avg points `14.1186`
  - Candidate B: trades `19`, net points `1769.25`, avg points `93.1184`
- Lectura persistida:
  - `Candidate B` reduce mucho la frecuencia, pero mejora la lectura comparativa orientativa de la rama principal en esta muestra.
- Dictamen final persistido:
  - `keep_candidate_B`
- Artefactos creados:
  - `mgf-control/COMB_001_candidate_A_decision.md`
  - `mgf-control/COMB_001_candidate_B_impl.md`
  - `mgf-control/COMB_001_candidate_B_rules.md`
  - `mgf-control/COMB_001_candidate_B_comparison.md`
  - `mgf-control/COMB_001_candidate_B_summary.md`
- `phase_state.json` actualizado para reflejar que `Candidate B` queda seleccionado provisionalmente como variante de trabajo.
- No se abrieron nuevas ramas.
- No se abrió backtest definitivo.
- Siguiente acción válida: si se autoriza, promover `Candidate B` como variante actual de trabajo de `COMB_001`.

## 2026-04-16 10:05 UTC
- Corrección de estado persistido aplicada para alinear la prioridad operativa con la estructura de ramas aprobada.
- `COMB_001` base queda explícitamente como matriz/base principal del proyecto.
- `Candidate B` queda explícitamente como rama derivada activa.
- `EL_STPMT_DIV` y `EL_REPULSE_DIV` conservan su estado histórico `PASS` en Fase 2/Fase 3, pero ya no figuran como prioridad operativa actual.
- `phase_state.json` corregido para que:
  - `current_focus` apunte a `COMB_001 Candidate B`
  - `next_allowed_action` apunte a preparar o ejecutar `Candidate B1`
- `session_checkpoint.md` y `night_run_summary.md` actualizados en la misma línea.
- No se abrió Fase 4.
- No se abrieron nuevas combinaciones.
- No se rehizo trabajo ya completado.
- Próxima unidad válida: preparar o ejecutar `Candidate B1`, manteniendo visible la referencia contra `COMB_001` base.

## 2026-04-16 10:01 UTC
- Run autónomo ejecutado solo con archivos de estado del proyecto.
- Inconsistencia real corregida:
  - `phase_state.json` seguía con `last_updated_utc` desfasado respecto al último estado persistido del 2026-04-16 y todavía dejaba `Candidate B` solo como seleccionado provisionalmente.
- Reevaluación inmediata posterior:
  - no hay aprobación abierta;
  - no hay blocker real;
  - la siguiente unidad válida ya persistida era promover `Candidate B` como variante actual de trabajo de `COMB_001`.
- Unidad ejecutada:
  - `COMB_001 Candidate B` queda promovido como variante actual de trabajo de la rama principal.
- Sincronización aplicada:
  - `phase_state.json` actualizado con el nuevo foco activo y timestamp coherente.
- No se abrió `Fase 4`.
- No se hizo backtest.
- Siguiente acción válida: preparar la siguiente iteración controlada con `Candidate B` como baseline, solo si hay autorización explícita.

## 2026-04-15 19:01 UTC
- Run autónomo limitado a archivos de estado del proyecto.
- Inconsistencia administrativa real detectada y corregida:
  - `approval_request.md` y `phase_state.json` ya apuntaban a `market_data_acquisition_for_SPY_15m_2023_2024`, pero `approval_queue.md` seguía arrastrando la solicitud antigua de apertura de `Fase 4`.
- Sincronización aplicada:
  - `approval_queue.md` actualizado para reflejar la aprobación realmente abierta de adquisición/carga de datos de mercado.
- Reevaluación inmediata posterior:
  - sigue existiendo un gate real de aprobación explícita antes de cualquier carga local o descarga real del dataset;
  - `awaiting_user_approval = true`;
  - no hay unidad técnica válida ejecutable sin violar ese gate.
- El run se detiene aquí tras persistir estado coherente.
- Notificación pendiente: Telegram al usuario indicando que el proyecto sigue esperando aprobación explícita para `market_data_acquisition_for_SPY_15m_2023_2024`.

## 2026-04-15 20:01 UTC
- Run autónomo limitado a archivos de estado del proyecto.
- Inconsistencia administrativa real detectada y corregida:
  - `approval_request.md` y `approval_queue.md` seguían marcando una aprobación abierta para `market_data_acquisition_for_MNQ_10m_2023_2024`.
  - El checkpoint más reciente ya dejaba esa aprobación consumida y el intento en `FAIL_BLOCK` por falta de dataset local apto.
- Sincronización aplicada:
  - `approval_request.md` cerrado como `no_open_request`.
  - `approval_queue.md` actualizado a `0 aprobaciones abiertas`.
  - `phase_state.json` regrabado con timestamp actual sin cambiar el blocker real.
- Reevaluación inmediata posterior:
  - persiste un blocker real por ausencia de dataset local correcto para `MNQ 10m 2023-01-01 -> 2024-12-31`;
  - no existe aprobación abierta vigente;
  - no hay unidad técnica válida en Fase 2 o Fase 3 sin aportar dataset local correcto o autorizar descarga externa concreta.
- El run se detiene aquí tras dejar el estado coherente.

## 2026-04-15 21:01 UTC
- Run autónomo limitado a archivos de estado del proyecto.
- Inconsistencia administrativa real detectada y corregida:
  - `phase_state.json` seguía mezclando un `current_focus` de trabajo metodológico de backtest con `phase_4 = not_authorized`.
  - El estado persistido de componentes prioritarios ya deja `EL_STPMT_DIV` y `EL_REPULSE_DIV` completos en Fase 2 y Fase 3.
- Sincronización aplicada:
  - `phase_state.json` actualizado para reflejar que el conjunto prioritario actual está completo en Fase 2/Fase 3;
  - `phase_4` queda marcado como trabajo ya corrido en modo ligero con fix metodológico pendiente, pero cualquier trabajo nuevo de Fase 4 sigue requiriendo aprobación explícita.
- Reevaluación inmediata posterior:
  - no hay aprobación abierta ahora mismo;
  - no existe unidad técnica válida en Fase 2 o Fase 3 para `EL_STPMT_DIV` o `EL_REPULSE_DIV` sin rehacer trabajo ya pasado;
  - el siguiente paso posible queda detrás de gate real de aprobación explícita para nuevo trabajo de `Fase 4`.
- El run se detiene aquí tras persistir estado coherente.
- Notificación pendiente: Telegram al usuario indicando que no hay trabajo válido adicional en Fase 2/Fase 3 y que cualquier avance nuevo requiere aprobación explícita para Fase 4.

## 2026-04-15 22:01 UTC
- Run autónomo limitado a archivos de estado del proyecto y reevaluación del standing order actual.
- Inconsistencia administrativa real detectada y corregida:
  - `phase_state.json` mantenía `current_focus` en desarrollo de `COMB_001` aunque el estado persistido más reciente ya deja `EL_STPMT_DIV` y `EL_REPULSE_DIV` cerrados en Fase 2/Fase 3 y sin aprobación abierta para trabajo nuevo de Fase 4.
  - `last_updated_utc` también quedó desfasado respecto al cierre administrativo más reciente.
- Sincronización aplicada:
  - `phase_state.json` actualizado para reflejar cierre de prioridades actuales en Fase 2/Fase 3;
  - siguiente acción válida fijada detrás del gate real de aprobación explícita antes de cualquier trabajo nuevo de Fase 4 o metodología de backtest.
- Reevaluación inmediata posterior:
  - `awaiting_user_approval = false` y no hay solicitud abierta;
  - no existe unidad técnica válida adicional sobre `EL_STPMT_DIV` o `EL_REPULSE_DIV` sin rehacer trabajo ya completado;
  - el flujo queda detenido por gate real de aprobación explícita para cualquier avance nuevo fuera de Fase 2/Fase 3.
- El run se detiene aquí tras persistir estado coherente.
- Notificación pendiente: Telegram al usuario indicando que el estado quedó sincronizado y que cualquier nueva unidad válida requiere aprobación explícita para Fase 4 o trabajo metodológico asociado.

## 2026-04-16 11:01 UTC
- Run autónomo limitado a archivos de estado del proyecto según el standing order actual.
- Inconsistencias reales detectadas y corregidas en `phase_state.json`:
  - `phase_3.status` seguía como `authorized_for_selected_components_with_pending_smoke` aunque `EL_STPMT_DIV` y `EL_REPULSE_DIV` ya figuran en `PASS` también en Fase 3.
  - `current_focus` seguía arrastrando trabajo de `COMB_001`, fuera de la prioridad vigente del standing order.
- Sincronización aplicada:
  - `phase_state.json` actualizado para reflejar que las prioridades actuales `EL_STPMT_DIV` y `EL_REPULSE_DIV` están cerradas en Fase 2/Fase 3;
  - siguiente acción válida fijada detrás de aprobación explícita antes de cualquier trabajo nuevo de Fase 4 o metodología/backtest.
- Reevaluación inmediata posterior:
  - no hay aprobaciones abiertas;
  - no existe unidad técnica válida adicional en Fase 2 o Fase 3 sobre `EL_STPMT_DIV` o `EL_REPULSE_DIV` sin rehacer trabajo ya completado;
  - existe gate real para cualquier avance nuevo fuera de ese cierre.
- El run se detiene aquí tras persistir estado coherente.
- Notificación pendiente: Telegram al usuario indicando que no hay unidad técnica válida adicional bajo el standing order actual y que cualquier avance nuevo requiere aprobación explícita para Fase 4 o trabajo metodológico asociado.
