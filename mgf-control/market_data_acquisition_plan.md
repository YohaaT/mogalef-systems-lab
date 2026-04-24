PHASE: control
OBJECTIVE: Preparar el plan mínimo de adquisición de datos para habilitar backtests reproducibles, sin descargar datos todavía y sin abrir `Fase 4`.
SCOPE: Plan de adquisición/ingesta local únicamente. Sin descarga real, sin transformación real, sin backtest.
INPUTS: `PROJECT_MASTER.md`, `TOKEN_POLICY.md`, `RUN_PROTOCOL.md`, `mgf-control/phase_state.json`, `mgf-control/market_data_requirements.md`, `mgf-control/backtest_first_minimal_strategy.md`.
EXPECTED ARTIFACT: `mgf-control/market_data_acquisition_plan.md`.
STOP CONDITION: detenerse al dejar el plan persistido.

# Market data acquisition plan

## 1. Objetivo del plan
Dejar preparado el camino mínimo para obtener o cargar el dataset local necesario para el primer backtest reproducible de la `first minimal combined strategy candidate`, sin descargar datos todavía.

## 2. Alcance
Este plan cubre solo:
- definición del símbolo inicial
- definición del timeframe inicial
- definición de sesión/horario
- formato local de almacenamiento
- validaciones mínimas antes del uso en backtest

No cubre todavía:
- descarga efectiva
- proveedores concretos no autorizados
- ampliación a múltiples símbolos
- ampliación a múltiples timeframes

## 3. Secuencia mínima propuesta
### Paso 1. Fijar instrumento inicial
Elegir y persistir un único símbolo inicial para la primera corrida.

Debe quedar explícito:
- `symbol`
- `exchange/venue` si aplica
- `asset_class`
- `timezone_local`

### Paso 2. Fijar timeframe inicial
Persistir el timeframe inicial recomendado:
- `15m`

### Paso 3. Fijar política de sesión
Persistir una sola política de sesión:
- usar la sesión principal del instrumento
- excluir barras fuera de sesión para la primera corrida
- timestamps almacenados en UTC

### Paso 4. Ingesta al formato canónico local
Cargar los datos en:
- `mgf-data/market/`

Formato canónico inicial:
- CSV

### Paso 5. Validación previa al uso
Antes de usarlo en backtest, correr validación mínima:
- orden temporal correcto
- sin duplicados
- OHLC coherente
- cobertura temporal documentada
- columnas requeridas presentes

### Paso 6. Registrar manifest o nota del dataset
Junto al dataset debe existir metadata mínima con:
- símbolo
- fuente
- rango temporal
- timeframe
- sesión
- timezone
- filas totales
- checksum/hash del archivo final

## 4. Estructura local recomendada
- `mgf-data/market/`
- `mgf-data/market/manifests/`

## 5. Convención de archivos recomendada
Dataset principal:
- `<symbol>__<bar_interval>__<session_name>__<start_utc>__<end_utc>.csv`

Manifest recomendado:
- `<symbol>__<bar_interval>__<session_name>__<start_utc>__<end_utc>.md`

## 6. Dataset mínimo suficiente para desbloqueo
Se considerará suficiente para desbloquear el rerun de `Fase 4` cuando exista al menos un archivo local que cumpla simultáneamente:
- símbolo inicial explícito
- timeframe `15m`
- sesión definida
- columnas OHLCV válidas
- rango temporal útil documentado
- validación básica aprobada

## 7. Riesgos a evitar
- usar datasets descargados sin documentar fuente y rango;
- mezclar sesiones sin regla fija;
- cambiar timeframe en mitad del proceso;
- usar CSV con timestamps ambiguos o timezone implícita;
- abrir backtest antes de validar integridad mínima.

## 8. Qué falta exactamente para desbloquear `Fase 4`
Faltan estas decisiones/artefactos concretos:
1. símbolo inicial explícito;
2. archivo local OHLCV en CSV canónico;
3. sesión/horario persistidos;
4. metadata/manifest del dataset;
5. validación mínima del dataset completada.

## 9. Siguiente paso autorizado recomendado
Sin descargar todavía datos, el siguiente paso autorizado natural sería:
- fijar explícitamente el símbolo inicial y dejar preparada la ruta/convención de ingesta local.

Result:
Artifacts created:
- `mgf-control/market_data_acquisition_plan.md`
Files read:
- `PROJECT_MASTER.md`
- `TOKEN_POLICY.md`
- `RUN_PROTOCOL.md`
- `mgf-control/phase_state.json`
- `mgf-control/market_data_requirements.md`
- `mgf-control/backtest_first_minimal_strategy.md`
Scope respected: yes
Next recommended action: esperar autorización para adquisición/carga de datos o fijación explícita del símbolo inicial.
