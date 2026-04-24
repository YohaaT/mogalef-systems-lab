PHASE: 4
OBJECTIVE: Corregir la metodología temporal del backtest ligero de la `first minimal combined strategy candidate` para eliminar posible lookahead y dejar una lectura más honesta.
SCOPE: Solo esta estrategia, solo el dataset práctico `MNQ 5m`, sin abrir otros sistemas, sin descargar datos nuevos.
INPUTS: `mgf-control/backtest_first_minimal_strategy.md`, `mgf-control/first_minimal_strategy_candidate.md`, `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`, implementaciones actuales de `EL_MOGALEF_Bands`, `EL_Mogalef_Trend_Filter_V2`, `EL_Stop_Intelligent`, `EL_STPMT_DIV`.
EXPECTED ARTIFACT: `mgf-control/backtest_fix_temporal_methodology.md`.
STOP CONDITION: detenerse al dejar la metodología temporal corregida y el rerun documentado.

# Backtest temporal methodology fix

## Convención temporal corregida
Para este rerun la convención pasa a ser explícitamente:
1. la señal se observa en barra cerrada `t`;
2. la entrada se ejecuta en la apertura de la barra siguiente `t+1`;
3. el stop empieza a aplicar solo después de la entrada real;
4. la salida por stop se evalúa barra a barra sin usar información futura para decidir la entrada;
5. una sola posición a la vez.

## Qué hace realmente esta estrategia
La estrategia intenta capturar giros/divergencias o continuaciones filtradas dentro de un contexto estructural razonable.

### En simple
- `EL_STPMT_DIV` busca el disparo de entrada.
- `EL_Mogalef_Trend_Filter_V2` decide si el régimen permite operar o no.
- `EL_MOGALEF_Bands` evita tomar entradas cuando el precio ya está demasiado fuera del contexto estructural.
- `EL_Stop_Intelligent` gestiona la salida de riesgo.

### Traducción operativa
La idea base es:
- **entrar solo cuando aparece señal de divergencia STPMT**, pero
- **solo si el filtro de tendencia/régimen no está bloqueando**, y
- **solo si el precio sigue dentro de un contexto de bandas razonable**, para evitar perseguir extensiones extremas,
- y una vez dentro, **dejar que el stop inteligente saque la posición**.

No lleva todavía:
- target fijo,
- filtros horarios extra,
- pyramiding,
- money management complejo,
- mezcla de múltiples motores de entrada.

## Nota
Este documento prepara el rerun corregido y deja clara la lógica operativa entendible de la estrategia.
