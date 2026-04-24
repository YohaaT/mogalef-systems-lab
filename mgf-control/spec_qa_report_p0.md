# spec_qa_report_p0

PHASE: 1
OBJECTIVE: Auditar documentalmente las specs p0_core existentes para decidir si están listas para Fase 2.
SCOPE: QA documental únicamente. Sin modificar specs. Sin Fase 2, sin rebuild, sin backtest, sin videos.
INPUTS: PROJECT_MASTER.md, TOKEN_POLICY.md, RUN_PROTOCOL.md y las specs p0_core existentes al momento del run.
EXPECTED ARTIFACT: mgf-control/spec_qa_report_p0.md
STOP CONDITION: Stop after the QA report is written and saved.

## Criterio de estado
- **PASS**: la spec está usable para Fase 2 tal como está, con observaciones menores no bloqueantes.
- **FIX**: la spec está cerca, pero requiere correcciones documentales antes de pasar a Fase 2.
- **BLOCK**: la spec no está suficientemente definida o contiene problemas que harían arriesgada la reconstrucción.

---

## 1) `mgf-bands-lab/spec/EL_MOGALEF_Bands.md`

**Estado:** PASS

**Errores detectados:**
- No se detecta mezcla de metadata de run en el documento actual.
- No se detectan contradicciones funcionales mayores.
- El pseudocódigo sigue siendo aproximado y no ejecutable tal cual para replicación exacta, pero está suficientemente limpio como guía.

**Nivel de gravedad:** menor

**Corrección recomendada:**
- Mantener la spec actual como referencia canónica.
- Si se desea mayor precisión antes de Fase 2, añadir una nota explícita sobre cómo inicializar `MogStopL/MogStopS` en primeras barras sin `next_j` válido.

**Acciones mínimas para quedar lista para Fase 2:**
- Ninguna obligatoria.
- Opcional: precisar tratamiento de primeras barras y valores `None` en la pasada retrospectiva.

**Observaciones QA por criterio:**
1. Metadata de run mezclada: no.
2. Inputs/outputs/series internas: claros.
3. Lógica barra a barra: completa.
4. Cambio de estado: claro.
5. Núcleo funcional vs visual/accesorio: sí, bien separado.
6. Ambigüedades: sí, bien declaradas.
7. Pseudocódigo: limpio y programable como guía.
8. Riesgo de lookahead/traducción: sí, bien documentado.
9. Contradicciones internas: no detectadas.
10. Lista para Fase 2: sí.

---

## 2) `mgf-stop-lab/spec/EL_Stop_Intelligent.md`

**Estado:** FIX

**Errores detectados:**
- Mezcla metadata de run con contenido funcional en el header inicial.
- No separa explícitamente núcleo funcional vs elementos visuales/accesorios.
- El riesgo de traducción por detección retrospectiva de pivots está mencionado, pero no queda documentado con la misma claridad que el riesgo de lookahead en la lógica de pivots confirmados.
- El pseudocódigo es razonable, pero simplifica `WaitForXtrem` y no modela explícitamente `HH0/BB0`, por lo que no es programable de forma fiel sin reabrir demasiadas decisiones.

**Nivel de gravedad:** medio

**Corrección recomendada:**
- Limpiar el header de run.
- Añadir bloque explícito de núcleo funcional vs accesorio.
- Añadir nota crítica de traducción sobre pivots confirmados con información a derecha y sobre `WaitForXtrem`.
- Ajustar pseudocódigo para reflejar `HH0`, `BB0` y la congelación por ruptura de extremo.

**Acciones mínimas para quedar lista para Fase 2:**
- Eliminar metadata de run.
- Documentar riesgo de confirmación retrospectiva/lookahead en pivots.
- Completar pseudocódigo de `WaitForXtrem`.
- Separar claramente lógica funcional de detalles de publicación/host (`SetStopPrice`).

**Observaciones QA por criterio:**
1. Metadata de run mezclada: sí.
2. Inputs/outputs/series internas: claros en general.
3. Lógica barra a barra: casi completa, pero `WaitForXtrem` queda resumido.
4. Cambio de estado: suficiente.
5. Núcleo funcional vs visual/accesorio: no explícito.
6. Ambigüedades: implícitas en notas finales, pero no estructuradas en la propia spec.
7. Pseudocódigo: útil, pero incompleto respecto a `WaitForXtrem` y fidelidad total.
8. Riesgo de lookahead/traducción: parcialmente documentado, no suficiente.
9. Contradicciones internas: no críticas.
10. Lista para Fase 2: todavía no; requiere fix documental.

---

## 3) `mgf-regime-filter-lab/spec/EL_Mogalef_Trend_Filter_V2.md`

**Estado:** FIX

**Errores detectados:**
- Mezcla metadata de run con contenido funcional en el header inicial.
- No separa explícitamente núcleo funcional vs elementos visuales/accesorios.
- Falta una sección formal de ambigüedades o referencia a archivo de ambigüedades dentro de la spec.
- Hay riesgo de traducción asociado a `open[L-1]` y a la reconstrucción retrospectiva de repulse, pero no está explicitado como riesgo de porting.
- El pseudocódigo es programable, pero no deja del todo clara la equivalencia exacta con la semántica retrospectiva del host original.

**Nivel de gravedad:** medio

**Corrección recomendada:**
- Limpiar header de run.
- Añadir separación núcleo funcional / accesorio, dejando `Plot(CAS)` y `sentiment` de interpretación como capa de salida.
- Añadir sección de ambigüedades y riesgo de traducción de `open_shifted`, EMA inicial y caducidad por fecha.

**Acciones mínimas para quedar lista para Fase 2:**
- Eliminar metadata de run.
- Añadir sección formal de ambigüedades.
- Documentar riesgo de traducción del repulse V2 y del umbral `CurrentBarIndex() < (R3 * 5)`.
- Separar explícitamente lógica de clasificación (`CAS`) de la política de bloqueo.

**Observaciones QA por criterio:**
1. Metadata de run mezclada: sí.
2. Inputs/outputs/series internas: claros.
3. Lógica barra a barra: clara.
4. Cambio de estado: suficientemente claro para un filtro de casos.
5. Núcleo funcional vs visual/accesorio: no explícito.
6. Ambigüedades: insuficientemente declaradas en la spec.
7. Pseudocódigo: limpio, bastante programable.
8. Riesgo de lookahead/traducción: presente, no bien documentado.
9. Contradicciones internas: no detectadas.
10. Lista para Fase 2: todavía no; requiere fix documental.

---

## 4) `mgf-regime-filter-lab/spec/EL_NeutralZone_B_V2.md`

**Estado:** FIX

**Errores detectados:**
- Mezcla metadata de run con contenido funcional en el header inicial.
- No separa explícitamente núcleo funcional vs elementos visuales/accesorios.
- No referencia explícitamente un archivo de ambigüedades.
- La lógica retrospectiva de `marqueurRET` y comparación con `i+1` tiene riesgo de traducción/lookahead no documentado.
- El output usa `RET` como nombre de serie y como nombre de parámetro de ventana, lo que puede ser confuso aunque no necesariamente contradictorio.

**Nivel de gravedad:** medio

**Corrección recomendada:**
- Limpiar header.
- Añadir bloque de núcleo funcional vs elementos visuales.
- Añadir nota crítica de traducción sobre marcadores retrospectivos y transición en modo `signal`.
- Aclarar en la spec la diferencia entre parámetro `RET` y serie `RET` o renombrar conceptualmente en la documentación (`ret_mid`, por ejemplo) sin cambiar la lógica.

**Acciones mínimas para quedar lista para Fase 2:**
- Eliminar metadata de run.
- Documentar explícitamente riesgo de lookahead/traducción retrospectiva.
- Declarar ambigüedades formales.
- Separar capa visual (`band`, `milieu` visible) de capa funcional (`senti`, marcadores).

**Observaciones QA por criterio:**
1. Metadata de run mezclada: sí.
2. Inputs/outputs/series internas: claros, con una colisión nominal moderada en `RET`.
3. Lógica barra a barra: clara.
4. Cambio de estado: claro.
5. Núcleo funcional vs visual/accesorio: no explícito.
6. Ambigüedades: no suficientemente declaradas.
7. Pseudocódigo: limpio y programable.
8. Riesgo de lookahead/traducción: no bien documentado.
9. Contradicciones internas: no críticas, pero hay ambigüedad de naming.
10. Lista para Fase 2: todavía no; requiere fix documental.

---

## 5) `mgf-divergence-lab/spec/EL_STPMT_DIV.md`

**Estado:** FIX

**Errores detectados:**
- Mezcla metadata de run con contenido funcional en el header inicial.
- No separa explícitamente núcleo funcional vs elementos visuales/accesorios.
- Aunque referencia un archivo de ambigüedades, la propia spec no incluye una nota crítica de traducción sobre construcción retrospectiva de STPMT y pivots.
- El pseudocódigo es útil como guía, pero delega demasiado en funciones placeholder (`detect_last_high_pivot`, etc.) para considerarse programable de forma inmediata.
- El documento no deja aislado con suficiente claridad qué parte pertenece a señal y qué parte a capa de alertas/visualización.

**Nivel de gravedad:** medio

**Corrección recomendada:**
- Limpiar header.
- Separar explícitamente núcleo funcional, visuales y alertas.
- Añadir nota crítica de riesgo de porting/lookahead.
- Bajar el nivel de abstracción del pseudocódigo o indicar explícitamente que es pseudocódigo estructural no ejecutable.

**Acciones mínimas para quedar lista para Fase 2:**
- Eliminar metadata de run.
- Documentar riesgo retrospectivo/lookahead.
- Separar alertas/plots de la lógica funcional.
- Completar pseudocódigo a nivel más implementable o acotar qué partes quedan delegadas.

**Observaciones QA por criterio:**
1. Metadata de run mezclada: sí.
2. Inputs/outputs/series internas: claros.
3. Lógica barra a barra: suficientemente completa.
4. Cambio de estado: claro.
5. Núcleo funcional vs visual/accesorio: no explícito.
6. Ambigüedades: sí, existen y están referenciadas.
7. Pseudocódigo: consistente, pero demasiado abstracto para implementación directa.
8. Riesgo de lookahead/traducción: no suficientemente documentado en la spec.
9. Contradicciones internas: no detectadas.
10. Lista para Fase 2: todavía no; requiere fix documental.

---

## 6) `mgf-divergence-lab/spec/EL_REPULSE_DIV.md`

**Estado:** FIX

**Errores detectados:**
- Mezcla metadata de run con contenido funcional en el header inicial.
- No separa explícitamente núcleo funcional vs elementos visuales/accesorios.
- La spec referencia ambigüedades, pero no declara dentro del cuerpo una nota crítica sobre indexing retrospectivo y semántica exacta de `Pose` persistente.
- El pseudocódigo es razonable, pero se apoya en `detect_divergences_for_three_horizons` sin describir suficiente detalle interno para implementación inmediata.
- Falta señalar de forma más explícita que el reescalado por `TickSize()` es accesorio visual y no parte nuclear de la decisión.

**Nivel de gravedad:** medio

**Corrección recomendada:**
- Limpiar header.
- Separar núcleo funcional, visualización y agregación de señal.
- Añadir nota crítica de traducción sobre índices retrospectivos y persistencia de `Pose`.
- Hacer el pseudocódigo más detallado o etiquetarlo claramente como estructural.

**Acciones mínimas para quedar lista para Fase 2:**
- Eliminar metadata de run.
- Añadir nota formal de riesgo de traducción/lookahead.
- Separar explícitamente lo visual del núcleo de señal.
- Mejorar fidelidad programable del pseudocódigo.

**Observaciones QA por criterio:**
1. Metadata de run mezclada: sí.
2. Inputs/outputs/series internas: claros.
3. Lógica barra a barra: clara.
4. Cambio de estado: suficiente.
5. Núcleo funcional vs visual/accesorio: no explícito.
6. Ambigüedades: sí, referenciadas.
7. Pseudocódigo: consistente, pero parcialmente abstracto.
8. Riesgo de lookahead/traducción: presente, no bien documentado en la spec.
9. Contradicciones internas: no detectadas.
10. Lista para Fase 2: todavía no; requiere fix documental.

---

## Resumen ejecutivo QA

### PASS
- `EL_MOGALEF_Bands`

### FIX
- `EL_Stop_Intelligent`
- `EL_Mogalef_Trend_Filter_V2`
- `EL_NeutralZone_B_V2`
- `EL_STPMT_DIV`
- `EL_REPULSE_DIV`

### BLOCK
- Ninguna en esta pasada.

## Conclusión general
El paquete p0_core está bastante avanzado a nivel documental, pero no todas las specs están listas de forma homogénea para Fase 2.

La principal causa de **FIX** no es falta de lógica de trading, sino deuda de especificación:
- headers de run incrustados,
- separación insuficiente entre núcleo funcional y elementos accesorios,
- riesgo de traducción/lookahead no siempre documentado,
- pseudocódigo a veces más estructural que directamente implementable.

`EL_MOGALEF_Bands` es actualmente la referencia más limpia y más cercana al estándar deseado para entrar en Fase 2.

Result:
Artifacts created:
- mgf-control/spec_qa_report_p0.md
Files read:
- PROJECT_MASTER.md
- TOKEN_POLICY.md
- RUN_PROTOCOL.md
- specs p0_core existentes al momento del run
Scope respected: yes
Next recommended action: ejecutar un run de limpieza documental sobre las specs en estado FIX, sin tocar todavía Fase 2.
