PHASE: 4
OBJECTIVE: Auditar la integración de componentes de la `first minimal combined strategy candidate` para detectar la fuente probable de sesgo temporal/lookahead.
SCOPE: Solo auditoría técnica de `EL_MOGALEF_Bands`, `EL_STPMT_DIV`, `EL_Stop_Intelligent` y su integración con `EL_Mogalef_Trend_Filter_V2` sobre el dataset práctico `MNQ 5m`.
INPUTS: `mgf-control/backtest_first_minimal_strategy.md`, `mgf-control/backtest_fix_temporal_methodology.md`, `mgf-control/first_minimal_strategy_candidate.md`, código fuente actual de los cuatro componentes, `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`.
EXPECTED ARTIFACT: `mgf-control/backtest_component_audit.md`.
STOP CONDITION: detenerse al dejar identificado el riesgo principal y sus implicaciones.

# Backtest component audit

## Resultado corto
Sí existe una fuente técnica fuerte de contaminación del backtest actual.

## Qué hace esta estrategia
La estrategia intenta operar `MNQ` usando cuatro capas:
1. `EL_STPMT_DIV` detecta una señal de entrada long/short.
2. `EL_Mogalef_Trend_Filter_V2` deja pasar o bloquea según régimen/tendencia.
3. `EL_MOGALEF_Bands` aporta contexto estructural para no entrar fuera del canal.
4. `EL_Stop_Intelligent` define la salida por stop.

Traducido a una frase:
> entra cuando aparece una divergencia STPMT compatible con el régimen y dentro de un contexto estructural razonable, y sale con stop dinámico.

## Hallazgo principal
Los mayores sospechosos no son `Trend Filter V2` ni la mera convención de entrada `t -> t+1`.
Los dos focos principales son:
- `EL_MOGALEF_Bands`
- `EL_Stop_Intelligent` en la forma actual de uso dentro del backtest

## Evidencia observada
### 1. `EL_MOGALEF_Bands`
La implementación reconstruida recorre de derecha a izquierda y hereda canal desde `j+1`.
Eso puede ser válido para replicar el indicador original, pero en contexto de estrategia significa que el canal visible en barras antiguas puede depender de información futura.

Señal observada en auditoría:
- `mog_h` y `mog_b` aparecen no nulos desde el arranque y muy estables en muestras tempranas.
- En varias señales tempranas aparece exactamente el mismo canal:
  - `mog_h = 27514.574977317643`
  - `mog_b = 22101.35229540937`

Eso es una bandera roja para uso estratégico barra a barra.

### 2. `EL_Stop_Intelligent`
El stop depende de una serie `market_position` completa, y su cálculo actual también recorre retrospectivamente.
Como indicador eso puede replicar el original, pero como motor de ejecución produce stops que ya nacen plenamente formados muy pronto en la serie cuando se le entrega una trayectoria de posición simplificada.

Señal observada en auditoría:
- primer índice no nulo de stop long: `0`
- primer índice no nulo de stop short: `0`
- en muestras tempranas se repiten niveles fijos muy pronto:
  - `stop_long = 26223.75`
  - `stop_short = 23103.8`

Eso es incompatible con un motor de stop que deba construirse secuencialmente solo con pasado conocido.

### 3. `EL_STPMT_DIV`
`EL_STPMT_DIV` también merece cautela, pero en esta auditoría no aparece como el principal culpable.
La primera señal `pose` aparece en índice `100`, lo cual al menos parece más plausible que los stops o bandas plenamente definidos desde el inicio.

### 4. `EL_Mogalef_Trend_Filter_V2`
El filtro parece el menos sospechoso en esta auditoría.
Su primer `pass` útil aparece bastante más tarde (`idx = 787`), coherente con un warmup grande por construcción.

## Conclusión técnica
El backtest actual está contaminado sobre todo porque estamos usando:
- un `Bands` reconstruido como indicador retrospectivo,
- y un `Stop Intelligent` reconstruido como indicador dependiente de trayectoria completa,
como si fueran directamente motores causales de estrategia.

Eso explica por qué incluso tras corregir la entrada a `t+1` las métricas siguieron absurdamente buenas.

## Dictamen de auditoría
- componente más problemático para estrategia: `EL_Stop_Intelligent`
- componente también problemático para estrategia: `EL_MOGALEF_Bands`
- componente menos sospechoso en esta pasada: `EL_Mogalef_Trend_Filter_V2`
- componente a revisar después: `EL_STPMT_DIV`

## Qué habría que hacer bien
Para un backtest honesto hay que construir wrappers causales de estrategia:
1. `Bands` causal, sin herencia desde futuro.
2. `Stop Intelligent` causal, actualizado barra a barra con posición viva real, no con trayectoria completa futura.
3. reconfirmar `STPMT_DIV` en modo puramente causal.

Hasta entonces, el resultado actual no sirve para inferir edge.

Result:
Artifacts created:
- `mgf-control/backtest_component_audit.md`
Files read:
- `mgf-control/backtest_first_minimal_strategy.md`
- `mgf-control/backtest_fix_temporal_methodology.md`
- `mgf-control/first_minimal_strategy_candidate.md`
- componentes base de estrategia
- `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`
Scope respected: yes
Next recommended action: diseñar wrappers causales de `Bands` y `Stop Intelligent` antes de cualquier nuevo rerun serio.
