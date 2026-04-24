PHASE: control
OBJECTIVE: Dejar preparada la unidad mínima de adquisición de datos, sin ejecutar todavía la descarga o carga real.
SCOPE: Un solo instrumento, un solo timeframe, una sola ruta local, una sola unidad de adquisición.
INPUTS: `PROJECT_MASTER.md`, `TOKEN_POLICY.md`, `RUN_PROTOCOL.md`, `mgf-control/phase_state.json`, `mgf-control/market_data_requirements.md`, `mgf-control/market_data_acquisition_plan.md`, `mgf-control/market_data_source_decision.md`.
EXPECTED ARTIFACT: `mgf-control/market_data_download_unit.md`.
STOP CONDITION: detenerse al dejar la unidad preparada sin ejecutar adquisición real.

# Market data download unit

## 1. Unidad preparada
Unidad mínima propuesta:
- instrumento: `MNQ`
- timeframe: `10m`
- rango temporal sugerido: `2023-01-01` a `2024-12-31`
- sesión: `regular_session`
- formato destino: `CSV`
- ruta destino: `mgf-data/market/MNQ__10m__regular_session__2023-01-01__2024-12-31.csv`

## 2. Método de adquisición definido
Ruta principal:
- carga o copia de un archivo local OHLCV previamente disponible y autorizado por el usuario.

Ruta alternativa, aún no autorizada:
- descarga desde un proveedor externo concreto que el usuario apruebe explícitamente.

## 3. Pasos de la unidad cuando quede autorizada
1. obtener o localizar el archivo fuente para `MNQ` `10m` `2023-01-01` a `2024-12-31`;
2. verificar que contiene al menos OHLCV y timestamps claros;
3. normalizar columnas al formato canónico del proyecto;
4. convertir timestamps a UTC si hace falta;
5. guardar el CSV canónico en la ruta destino;
6. generar manifest/nota mínima del dataset;
7. ejecutar validación mínima antes de considerarlo apto para backtest.

## 4. Resultado esperado de la unidad
- un archivo CSV canónico único;
- una ruta local estable y reproducible;
- un dataset listo para validación;
- sin abrir todavía el backtest.

## 5. Bloqueo actual de la unidad
No falta diseño técnico. Falta únicamente autorización de adquisición real.

## 6. Autorización pendiente exacta
Hace falta que el usuario autorice explícitamente una de estas dos acciones:
- `load_local_market_file_for_MNQ_10m_2023_2024`
- `download_external_market_data_for_MNQ_10m_2023_2024`

Sin una de esas aprobaciones, la unidad no debe ejecutarse.

Result:
Artifacts created:
- `mgf-control/market_data_download_unit.md`
Files read:
- `PROJECT_MASTER.md`
- `TOKEN_POLICY.md`
- `RUN_PROTOCOL.md`
- `mgf-control/phase_state.json`
- `mgf-control/market_data_requirements.md`
- `mgf-control/market_data_acquisition_plan.md`
- `mgf-control/market_data_source_decision.md`
Scope respected: yes
Next recommended action: abrir gate de aprobación para carga local o descarga externa del dataset definido.
