# Approval queue

Estado actual: 0 aprobaciones abiertas.

## Política
Solo registrar aquí solicitudes reales de aprobación cuando exista uno de estos gates:
- `Fase 3 -> Fase 4`
- bloqueo real
- trabajo caro o sensible
- cambio de arquitectura
- uso de videos
- backtest
- adquisición o descarga real de datos de mercado cuando aún no existe dataset local autorizado

## Regla vigente
`Fase 2 -> Fase 3` para componentes individuales con `PASS` al final de `Fase 2` ya no abre aprobación manual. Ese paso queda autoautorizado.

## Pendiente ahora
- ninguna

## Última solicitud cerrada
- `market_data_acquisition_for_MNQ_10m_2023_2024`
  - tipo: `adquisición/carga real de datos de mercado`
  - estado final: `approved_then_fail_block`
  - base: `mgf-control/market_data_download_unit.md`
  - destino esperado no creado: `mgf-data/market/MNQ__10m__regular_session__2023-01-01__2024-12-31.csv`
  - motivo de cierre: falta dataset local apto y no existe autorización adicional para descarga externa concreta
