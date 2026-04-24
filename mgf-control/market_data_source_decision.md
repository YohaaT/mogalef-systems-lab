PHASE: control
OBJECTIVE: Dejar decidida la fuente mínima de datos propuesta para habilitar un primer dataset local reproducible, sin ejecutar todavía la descarga.
SCOPE: Una sola fuente, un solo instrumento, un solo timeframe, una sola ruta local. Sin descarga real.
INPUTS: `PROJECT_MASTER.md`, `TOKEN_POLICY.md`, `RUN_PROTOCOL.md`, `mgf-control/phase_state.json`, `mgf-control/market_data_requirements.md`, `mgf-control/market_data_acquisition_plan.md`.
EXPECTED ARTIFACT: `mgf-control/market_data_source_decision.md`.
STOP CONDITION: detenerse al dejar la decisión de fuente persistida.

# Market data source decision

## 1. Fuente de datos propuesta
Fuente propuesta para la primera unidad mínima de adquisición:
- **archivo OHLCV local aportado o autorizado por el usuario**, normalizado luego al formato canónico del proyecto.

## 2. Motivo de esta decisión
Se mantiene esta vía como primera ruta porque:
- sigue siendo la más reproducible dentro del entorno actual;
- evita introducir dependencias externas no autorizadas;
- es coherente con un flujo de trabajo sobre futuros y posterior ejecución en NinjaTrader 8;
- permite validar primero la calidad del dataset antes de automatizar descargas desde proveedores externos.

## 3. Instrumento inicial exacto propuesto
Instrumento inicial propuesto:
- `MNQ`

## 4. Timeframe inicial exacto propuesto
Timeframe inicial propuesto:
- `10m`

## 5. Rango temporal inicial sugerido
Rango inicial sugerido:
- `2023-01-01` a `2024-12-31`

Motivo:
- suficiente para una primera corrida útil;
- evita una muestra demasiado corta;
- sigue siendo manejable en tamaño para validación manual inicial.

## 6. Formato local de almacenamiento
Formato canónico inicial:
- `CSV`

Ruta local canónica esperada:
- `mgf-data/market/`

## 7. Nombre y ruta esperada del archivo
Ruta esperada:
- `mgf-data/market/MNQ__10m__regular_session__2023-01-01__2024-12-31.csv`

## 8. Método de adquisición propuesto
Método propuesto para esta primera unidad:
1. recibir o localizar un archivo local de OHLCV del instrumento `MNQ` en `10m`;
2. normalizarlo a la estructura canónica del proyecto;
3. guardarlo en la ruta final indicada;
4. validar integridad mínima antes de habilitarlo para backtest.

## 9. Qué autorización falta exactamente
Falta una autorización explícita para ejecutar una de estas dos opciones:
- **cargar y normalizar un archivo local existente** si el usuario lo aporta o indica su ubicación;
- **descargar datos desde una fuente externa concreta** si el usuario prefiere esa vía y la autoriza explícitamente.

Mientras esa autorización no exista, no debe ejecutarse la adquisición real.

Result:
Artifacts created:
- `mgf-control/market_data_source_decision.md`
Files read:
- `PROJECT_MASTER.md`
- `TOKEN_POLICY.md`
- `RUN_PROTOCOL.md`
- `mgf-control/phase_state.json`
- `mgf-control/market_data_requirements.md`
- `mgf-control/market_data_acquisition_plan.md`
Scope respected: yes
Next recommended action: preparar la unidad de descarga/carga local y dejar el gate de aprobación listo sin ejecutar la adquisición.
