# Next strategy candidate

## Propósito
Dejar registrada una propuesta mínima de combinación para un futuro backtest, sin abrir `Fase 4` ahora.

## Primera estrategia mínima combinada propuesta
- componente estructural: `EL_MOGALEF_Bands`
- filtro: `EL_Mogalef_Trend_Filter_V2`
- salida/riesgo: `EL_Stop_Intelligent`

## Justificación breve
`EL_MOGALEF_Bands` por sí solo no constituye estrategia completa.
La primera combinación de valor razonable para futuro backtest debería unir:
- una estructura de canal/base,
- un filtro de régimen,
- una lógica de salida y gestión del riesgo.

## Secuencia previa necesaria antes de considerar backtest
1. cerrar `Fase 2` de `EL_Stop_Intelligent`
2. cerrar `Fase 2` de `EL_Mogalef_Trend_Filter_V2`
3. hacer sus smoke tests correspondientes cuando toque
4. solo después evaluar autorización de una combinación mínima para backtest

## Estado
- propuesta solamente
- no autorizada para backtest
- no implica apertura de `Fase 4`
