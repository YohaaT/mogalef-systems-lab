# Approval request

Estado: no_open_request

## Política vigente de gates
`Fase 2 -> Fase 3` queda autorizada automáticamente para componentes individuales que ya terminaron `Fase 2` en `PASS`.

## Gates que sí requieren aprobación explícita
- `Fase 3 -> Fase 4`
- bloqueos reales
- trabajo caro o sensible
- cambios de arquitectura
- uso de videos
- backtests
- adquisición o descarga real de datos de mercado cuando aún no existe dataset local autorizado

## Última solicitud procesada
- Solicitud: `market_data_acquisition_for_MNQ_10m_2023_2024`
- Tipo: adquisición/carga real de datos de mercado
- Resultado: aprobación consumida y ejecución intentada
- Dictamen operativo: `FAIL_BLOCK`
- Motivo persistido: no existe dataset local apto para `MNQ 10m 2023-01-01 -> 2024-12-31` y no hay autorización adicional para descarga externa concreta
- Ruta objetivo no creada: `mgf-data/market/MNQ__10m__regular_session__2023-01-01__2024-12-31.csv`
- Siguiente gate posible, si el usuario lo decide: autorización explícita para una descarga externa concreta de ese dataset exacto o aporte de archivo local correcto

## awaiting_user_approval
false
