PHASE: control
OBJECTIVE: Dejar una nota explícita de alcance para el dataset `MNQ 5m` obtenido en este run.
SCOPE: Nota de uso y limitaciones. Sin backtest.
INPUTS: dataset descargado y reporte de validación.
EXPECTED ARTIFACT: `mgf-control/market_data_scope_note.md`.
STOP CONDITION: detenerse al dejar la nota persistida.

# Market data scope note

## Alcance autorizado y real
El dataset obtenido en este run queda aceptado como base de trabajo práctica para:
- pruebas técnicas
- smoke tests
- validación funcional
- backtests ligeros

## Lo que este dataset no afirma
Este dataset no debe interpretarse por sí solo como:
- validación histórica definitiva del sistema;
- sustituto permanente de una cobertura histórica más larga;
- evidencia suficiente para conclusiones fuertes de robustez.

## Límite real de la fuente en este entorno
La fuente viable disponible en este entorno entregó solo una ventana intradía reciente de `MNQ 5m`.
No entregó de forma honesta el histórico `MNQ 10m 2023-2024` originalmente deseado.

## Implicación práctica
El dataset sí es útil para avanzar trabajo técnico y validación operativa ligera.
Si más adelante se necesita una validación más robusta, habrá que adquirir una fuente con mayor retención histórica o cobertura contractual más adecuada.

Result:
Artifacts created:
- `mgf-control/market_data_scope_note.md`
Files read:
- dataset `MNQ 5m` obtenido en este run
- `mgf-control/market_data_validation_report.md`
Scope respected: yes
Next recommended action: usar este dataset solo dentro del alcance práctico autorizado.
