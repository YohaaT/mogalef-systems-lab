# Optimization Documentation Alignment Note

**Fecha:** 2026-04-24  
**Contexto:** revisión documental del repositorio con foco en optimización, principalmente `UNIVERSAL_OPTIMIZATION_FRAMEWORK_v1.md`, `QUICK_START_OPTIMIZATION.md`, `COMB_002_IMPULSE_PHASE_CONFIG.json` y artefactos reales en `mgf-control/`.

## Resumen

La documentación de optimización del repo tiene una base metodológica coherente, pero hoy mezcla:

1. **Doctrina / intención canónica**
   - `mgf-control/MOGALEF_PDF_NOTES.md`
   - `UNIVERSAL_OPTIMIZATION_FRAMEWORK_v1.md`
   - `mgf-control/COMB_002_IMPULSE_PHASE_CONFIG.json`

2. **Campañas de optimización históricas o alternativas**
   - Resultados `COMB002_phase*_*_best_params.json`
   - `PHASE2_OPTIMIZATION_README.md`
   - scripts y consolidadores de `mgf-control/`

La inconsistencia observada parece venir de **optimizaciónes distintas ejecutadas en momentos diferentes**, no necesariamente de un error único de implementación. Aun así, conviene dejarlo documentado y etiquetado para evitar confusión futura.

## Observaciones principales

### 1. UOF v1 y las notas del PDF están mayormente alineados

Para `COMB_002_IMPULSE`, tanto el marco universal como las notas extraídas del PDF coinciden en lo esencial:

- Fase 1: optimizar señal.
- Fase 2: optimizar filtros de contexto sin mezclar fases.
- Fase 3: optimizar exits.
- Fase 4: optimizar stops.
- Validación walk-forward con `Phase A` / `Phase B`.
- Robustness como criterio de aceptación.
- `COMB_002`:
  - **sin trend filter**
  - **sin volatility filter**
  - **con filtro horario**
  - **con filtro diario**
  - **con Intelligent Scalping Target**
  - **con SuperStop**

### 2. La capa operativa del repo no siempre sigue esa versión canónica

En `mgf-control/` aparecen evidencias de flujos alternativos para `COMB_002`, por ejemplo:

- una `Phase 2` dividida en variantes `2a / 2b / 2c / 2d`;
- optimización de **volatility filter** en algunos artefactos;
- consolidaciones que priorizan `horaire + volatility` y no siempre reflejan `weekday` como parte final consolidada.

Esto entra en tensión con la doctrina Mogalef documentada para `COMB_002`, donde el filtro de volatilidad se considera perjudicial para la versión impulso.

### 3. Hay resultados con robustness alta pero muestra demasiado pequeña

Algunos artefactos muestran ratios de robustness muy altos con muy pocos trades en `Phase A` / `Phase B`. Eso puede ser útil como registro histórico, pero no debería confundirse con una validación robusta de producción.

## Interpretación recomendada

La lectura recomendada del repo debería ser:

- **Canónico / doctrina objetivo**:
  - `mgf-control/MOGALEF_PDF_NOTES.md`
  - `UNIVERSAL_OPTIMIZATION_FRAMEWORK_v1.md`
  - `mgf-control/COMB_002_IMPULSE_PHASE_CONFIG.json`

- **Histórico / experimental / campañas previas**:
  - `PHASE2_OPTIMIZATION_README.md`
  - `COMB002_phase*_*_best_params.json`
  - scripts de ejecución y consolidación usados en corridas específicas

## Recomendación de organización

Para dejar esto mejor documentado, conviene:

1. Etiquetar explícitamente cada artefacto como uno de estos tipos:
   - `canonical`
   - `experimental`
   - `historical-run`
   - `deprecated`

2. Indicar en cada README o consolidación:
   - qué estrategia exacta representa;
   - si sigue o no la doctrina Mogalef;
   - qué filtros están activos;
   - si el resultado es apto para producción o solo comparativo.

3. Mantener una única referencia “fuente de verdad” por estrategia:
   - para `COMB_002`, definir claramente cuál es el flujo canónico vigente.

## Conclusión

La inconsistencia documental observada **sí tiene explicación razonable**: coexistencia de optimizaciones distintas. Aun así, merece quedar registrada para que futuras revisiones no interpreten como “oficial” cualquier artefacto operativo histórico.

Esta nota no invalida los resultados previos; solo propone separarlos mejor entre **doctrina canónica** y **ejecuciones experimentales o históricas**.
