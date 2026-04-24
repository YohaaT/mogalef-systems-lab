# EL_NeutralZone_B_V2

## Propósito
Definir una zona neutra basada en la media entre una EMA larga y el punto medio del rango extremo reciente. El componente puede usarse como filtro continuo o como señal discreta de cambio de sesgo. También permite invertir el sentido operativo compra/venta.

## Contexto en catálogo
- canonical_name: `EL_NeutralZone_B_V2`
- family: `mgf-regime-filter-lab`
- subfamily: `neutral-zone`
- role: `filter`
- priority: `p0_core`
- status previo en catálogo: `classified`
- variante base: `EL_NeutralZone`

## Inputs

### Parámetros declarados
- `UseAs` (`signal;filter`, default `filter`): define si el componente actúa como filtro persistente o como disparador puntual por cambio de estado.
- `MMEperiod` (`1..200`, default `150`): periodo de la EMA del cierre.
- `RET` (`90..540`, default `90`): ventana de extremos para el punto medio estructural.
- `TrendIndicSize` (`1..100`, default `15`): desplazamiento visual de la banda de tendencia en ticks.
- `VueTrend` (`Yes;No`, default `Yes` por índice `0`): controla si se dibuja la banda de tendencia alrededor del medio.
- `Sens` (`Normal;Inverse`, default `Normal`): invierte o no el significado operativo alcista/bajista.

### Series de mercado
- `high`, `low`, `close`
- `TickSize()`
- índice de barra actual

## Outputs

### Núcleo funcional
- `line`: EMA del cierre.
- `ret_mid`: punto medio del máximo y mínimo de la ventana extrema. En el fuente original la serie también se llama `RET`, igual que el parámetro.
- `senti`: serie de sentimiento con valores observados `100`, `50`, `0`.
  - `100`: sesgo alcista o permiso de compra.
  - `50`: neutro o sin señal.
  - `0`: sesgo bajista o permiso de venta.

### Elementos visuales y accesorios
- `milieu`: media entre `line` y `ret_mid` cuando la vista de tendencia está activa.
- `band`: banda visual desplazada hacia arriba o abajo según el sesgo.

## Series internas
- `haut`: máximo rolling en ventana `RET`.
- `bas`: mínimo rolling en ventana `RET`.
- `marqueurRET`: dirección persistente del `ret_mid`, `1` si sube, `-1` si baja.
- `marqueurMME`: dirección persistente de la EMA, `1` si sube, `-1` si baja.

## Cálculo base

### 1. EMA principal
En la primera barra se inicializa:
- `line = EMA(close, MMEperiod)`

### 2. Eje estructural
Para cada barra:
- `haut = Highest(high, RET_window)`
- `bas = Lowest(low, RET_window)`
- `ret_mid = (haut + bas) / 2`

Interpretación funcional:
- `ret_mid` es el centro del rango extremo reciente, no una media de precios intermedios.
- `line` captura tendencia suavizada del cierre.
- la zona neutra real es el espacio entre ambos, resumido por su punto medio `milieu`.

### 3. Punto medio de la zona neutra
Si `VueTrend = Yes` (valor interno `0` en el código):
- `milieu = (ret_mid + line) / 2`

Si `VueTrend = No`:
- `milieu = void`

## Detección de dirección
En la pasada final sobre la historia:
- si `ret_mid[i] > ret_mid[i+1]`, entonces `marqueurRET[i] = 1`
- si `ret_mid[i] < ret_mid[i+1]`, entonces `marqueurRET[i] = -1`
- si no cambia, hereda el valor previo (`marqueurRET[i+1]`)

Para la EMA:
- si `line[i] >= line[i+1]`, entonces `marqueurMME[i] = 1`
- si `line[i] < line[i+1]`, entonces `marqueurMME[i] = -1`

Esto crea dos marcadores de dirección persistente: uno estructural y uno tendencial.

## Reglas de estado

### Estado alcista confirmado
Condición:
- `marqueurRET = 1`
- `marqueurMME = 1`

Efectos visuales:
- `band = milieu + ticksize * TrendIndicSize`

Efectos operativos en modo filtro:
- `Sens = Normal` -> `senti = 100`
- `Sens = Inverse` -> `senti = 0`

Efectos operativos en modo señal:
- por defecto `senti = 50`
- solo lanza señal si en la barra previa alguno de los marcadores no era alcista
- si hay cambio de estado, entonces:
  - `Sens = Normal` -> `senti = 100`
  - `Sens = Inverse` -> `senti = 0`

### Estado bajista confirmado
Condición:
- `marqueurRET = -1`
- `marqueurMME = -1`

Efectos visuales:
- `band = milieu - ticksize * TrendIndicSize`

Efectos operativos en modo filtro:
- `Sens = Normal` -> `senti = 0`
- `Sens = Inverse` -> `senti = 100`

Efectos operativos en modo señal:
- por defecto `senti = 50`
- solo lanza señal si en la barra previa alguno de los marcadores no era bajista
- si hay cambio de estado, entonces:
  - `Sens = Normal` -> `senti = 0`
  - `Sens = Inverse` -> `senti = 100`

### Estado neutro o mixto
Si los dos marcadores no apuntan en la misma dirección:
- `band` queda en `milieu`
- `senti = 50`

## Diferencia clave entre `filter` y `signal`

### Modo filtro
Mantiene un sesgo persistente mientras EMA y `ret_mid` suban juntos o bajen juntos.

### Modo señal
Solo emite `100` o `0` en la barra donde se confirma el cambio conjunto de dirección. Después vuelve a `50` hasta la próxima transición.

## Núcleo funcional vs elementos visuales/accesorios
Núcleo funcional del componente:
- cálculo de EMA del cierre
- cálculo de `haut`, `bas` y `ret_mid`
- cálculo de `marqueurRET` y `marqueurMME`
- generación de `senti` en modo `filter` o `signal`
- inversión semántica por `Sens`

Elementos visuales y accesorios:
- `milieu`
- `band`
- cualquier uso gráfico de `TrendIndicSize`
- la ocultación visual ligada a `VueTrend`

## Lógica barra a barra
1. Inicializa EMA del cierre una vez.
2. Calcula rolling highest y lowest sobre la ventana RET.
3. Calcula `ret_mid` como centro del rango extremo.
4. Recorre la historia de la última barra a la primera.
5. Reinicia `senti[i] = 50`.
6. Actualiza `marqueurRET` y `marqueurMME` comparando con la barra siguiente.
7. Calcula `milieu` y `band`.
8. Si ambos marcadores suben, genera estado alcista.
9. Si ambos marcadores bajan, genera estado bajista.
10. Si `UseAs = signal`, convierte el estado persistente en pulso de transición.
11. Aplica inversión si `Sens = Inverse`.
12. Publica `Sentiment = senti`.

## Dependencias
- EMA del cierre.
- rolling highest y lowest.
- `TickSize()`.
- representación de `void` para ocultar `milieu` cuando la banda de tendencia no se desea ver.

## Nota crítica de traducción
La dirección del componente se define retrospectivamente comparando cada barra con `i+1`. Eso crea un riesgo claro de porting:
- una implementación forward-only puede desplazar el momento exacto del cambio de estado,
- y el modo `signal` depende precisamente de esa transición entre la barra actual y la siguiente en el recorrido retrospectivo.

Además, el fuente reutiliza el nombre `RET` tanto para el parámetro como para la serie calculada. En esta spec se usa `ret_mid` para desambiguar documentalmente, pero sin cambiar la lógica observada del componente.

La reconstrucción de Fase 2 deberá documentar cómo replica:
- la herencia de `marqueurRET` cuando no hay cambio,
- la emisión del pulso en `UseAs=signal`,
- y el comportamiento visual cuando `VueTrend=No`.

## Ambigüedades
Las ambigüedades abiertas se documentan en:
- `mgf-regime-filter-lab/notes/EL_NeutralZone_B_V2_ambiguities.md`

## Pseudocódigo Python
```python
class NeutralZoneBV2:
    def __init__(
        self,
        mme_period=150,
        ret_window=90,
        trend_indic_size=15,
        use_as="filter",
        show_trend=True,
        sens="normal",
    ):
        self.mme_period = mme_period
        self.ret_window = ret_window
        self.trend_indic_size = trend_indic_size
        self.use_as = use_as
        self.show_trend = show_trend
        self.sens = sens

    def ema(self, values, period):
        out = [None] * len(values)
        alpha = 2.0 / (period + 1.0)
        for i, v in enumerate(values):
            out[i] = v if i == 0 else alpha * v + (1 - alpha) * out[i - 1]
        return out

    def rolling_high(self, values, window):
        out = [None] * len(values)
        for i in range(len(values)):
            if i + 1 >= window:
                out[i] = max(values[i - window + 1 : i + 1])
        return out

    def rolling_low(self, values, window):
        out = [None] * len(values)
        for i in range(len(values)):
            if i + 1 >= window:
                out[i] = min(values[i - window + 1 : i + 1])
        return out

    def compute(self, high, low, close, tick_size):
        line = self.ema(close, self.mme_period)
        haut = self.rolling_high(high, self.ret_window)
        bas = self.rolling_low(low, self.ret_window)
        ret_mid = [
            None if haut[i] is None or bas[i] is None else (haut[i] + bas[i]) / 2.0
            for i in range(len(close))
        ]

        milieu = [None] * len(close)
        band = [None] * len(close)
        marker_ret = [None] * len(close)
        marker_mme = [None] * len(close)
        senti = [50] * len(close)

        for i in range(len(close) - 1, -1, -1):
            next_i = i + 1
            if ret_mid[i] is None:
                continue

            if next_i < len(close):
                marker_ret[i] = marker_ret[next_i]
                if ret_mid[next_i] is not None:
                    if ret_mid[i] > ret_mid[next_i]:
                        marker_ret[i] = 1
                    elif ret_mid[i] < ret_mid[next_i]:
                        marker_ret[i] = -1
                marker_mme[i] = 1 if line[i] >= line[next_i] else -1

            if self.show_trend:
                milieu[i] = (ret_mid[i] + line[i]) / 2.0
            else:
                milieu[i] = None

            band[i] = milieu[i]

            bullish = marker_ret[i] == 1 and marker_mme[i] == 1
            bearish = marker_ret[i] == -1 and marker_mme[i] == -1

            if bullish:
                if milieu[i] is not None:
                    band[i] = milieu[i] + tick_size * self.trend_indic_size
                senti[i] = 100 if self.sens == "normal" else 0
                if self.use_as == "signal":
                    senti[i] = 50
                    prev_bull = (
                        next_i < len(close)
                        and marker_ret[next_i] == 1
                        and marker_mme[next_i] == 1
                    )
                    if not prev_bull:
                        senti[i] = 100 if self.sens == "normal" else 0

            elif bearish:
                if milieu[i] is not None:
                    band[i] = milieu[i] - tick_size * self.trend_indic_size
                senti[i] = 0 if self.sens == "normal" else 100
                if self.use_as == "signal":
                    senti[i] = 50
                    prev_bear = (
                        next_i < len(close)
                        and marker_ret[next_i] == -1
                        and marker_mme[next_i] == -1
                    )
                    if not prev_bear:
                        senti[i] = 0 if self.sens == "normal" else 100

        return {
            "line": line,
            "ret_mid": ret_mid,
            "milieu": milieu,
            "band": band,
            "senti": senti,
            "marqueurRET": marker_ret,
            "marqueurMME": marker_mme,
        }
```

## Notas de implementación futura
- La implementación Python deberá separar con claridad visualización y lógica para que `VueTrend=No` no anule accidentalmente la señal.
- Este componente es más limpio si se modela como consenso entre pendiente de EMA y pendiente de punto medio extremo, no como breakout.
- La versión base `EL_NeutralZone` confirma que V2 añade `UseAs`, `Sens`, `TrendIndicSize` configurable y mejor control visual.
