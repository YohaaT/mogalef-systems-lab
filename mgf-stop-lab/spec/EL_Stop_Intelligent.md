# EL_Stop_Intelligent

## Propósito
Definir un stop dinámico para posiciones largas o cortas usando pivots recientes de precio y un colchón de volatilidad adaptativo. El stop nunca se aleja de la posición abierta. Solo se acerca o permanece congelado hasta que aparezca un nuevo extremo relevante o se cumpla la condición opcional de esperar ruptura del último extremo.

## Contexto en catálogo
- canonical_name: `EL_Stop_Intelligent`
- family: `mgf-stop-lab`
- subfamily: `intelligent-family`
- role: `stop`
- priority: `p0_core`
- status previo en catálogo: `classified`
- variante relacionada: `EL_Stop_Intel_v2_live`
- derivado relacionado: `EL_Stop_Intelligent_target`

## Inputs

### Parámetros declarados
- `Quality` (`1..3`, default `2`): severidad del pivot detectado. Controla cuántas velas a izquierda y derecha deben confirmar un alto o bajo.
- `RecentVolat` (`1..3`, default `2`): ventana corta de ATR simple.
- `RefVolat` (`10..50`, default `20`): ventana de ATR de referencia.
- `CoefVolat` (`1..30`, default `5`): multiplicador del espacio adicional de volatilidad.
- `FirstLowOrMore` (`1..3`, default `2`): para largos, toma el mínimo entre los últimos 1, 2 o 3 bajos detectados.
- `FirstHighOrMore` (`1..3`, default `2`): para cortos, toma el máximo entre los últimos 1, 2 o 3 altos detectados.
- `WaitForXtrem` (`0..3`, default `0`): si es mayor que cero, no permite mover el stop hasta que precio supere el extremo almacenado correspondiente.

### Series de mercado
- `open`, `high`, `low`, `close`
- `MarketPosition()` con valores esperados `1`, `-1`, `0`
- índice de barra actual

## Outputs

### Núcleo funcional
- `stoplong`: serie del nivel activo de stop. En el fuente original se reutiliza tanto para largos como para cortos.

### Elementos de publicación y accesorios
- `SetStopPrice(stoplong)`: orden stop publicada cuando hay posición.
- cualquier separación semántica futura entre `stop_long_active` y `stop_short_active` sería una mejora documental o de implementación, no un cambio de lógica funcional.

## Series internas
- `tr`: true range barra a barra.
- `avtr`: ATR simple reciente.
- `avtrref`: ATR simple de referencia.
- `space`: colchón adicional de volatilidad.
- `haut`, `bas`: flags de detección de pivots altos y bajos.
- `H1`, `H2`, `H3`: últimos altos confirmados almacenados.
- `B1`, `B2`, `B3`: últimos bajos confirmados almacenados.
- `H0`, `B0`: alto o bajo base usado para construir el stop actual.
- `HH0`, `BB0`: extremos de espera usados por `WaitForXtrem`.
- `stlong`: candidato de stop bruto antes de la regla monotónica. En el fuente también se reutiliza como auxiliar del lado corto.
- `flaglong`: memoria de dirección de posición previa, con `1` para largo y `-1` para corto.

## Cálculo de volatilidad
El indicador calcula `tr` manualmente barra a barra como el máximo de:
- `high - low`
- `abs(close_prev - low)`
- `abs(high - close_prev)`

Después aplica medias móviles simples:
- `avtr = SMA(tr, RecentVolat)`
- `avtrref = SMA(tr, RefVolat)`

## Cálculo de `space`
`space = (((2 * avtrref) - avtr) * CoefVolat) / 5`

Interpretación funcional:
- si la volatilidad reciente cae por debajo de la de referencia, el stop deja más margen;
- si la volatilidad reciente sube, el margen se estrecha;
- el término puede ser negativo en casos extremos, por eso el código usa `absvalue(space)` en los clamps finales.

## Detección de pivots
La detección se hace retrospectivamente, solo en `isfinalbar()`, por lo que usa confirmación a derecha.

### `Quality = 1`
- alto confirmado si la barra `i+1` es un máximo local simple o una meseta corta.
- bajo confirmado si la barra `i+1` es un mínimo local simple o una meseta corta.
- se guarda el precio de `high[i+1]` o `low[i+1]`.

### `Quality = 2`
- alto confirmado si la barra `i+2` domina dos barras a izquierda y dos a derecha.
- bajo confirmado si la barra `i+2` domina dos barras a izquierda y dos a derecha.
- se guarda `high[i+2]` o `low[i+2]`.

### `Quality = 3`
- alto confirmado si la barra `i+3` domina tres barras a izquierda y tres a derecha.
- bajo confirmado si la barra `i+3` domina tres barras a izquierda y tres a derecha.
- se guarda `high[i+3]` o `low[i+3]`.

## Almacenamiento de extremos
Cada vez que aparece un pivot nuevo:
- para altos: `H3 <- H2`, `H2 <- H1`, `H1 <- nuevo_alto`
- para bajos: `B3 <- B2`, `B2 <- B1`, `B1 <- nuevo_bajo`

Si no aparece pivot, las series se heredan sin cambio desde la barra siguiente.

## Lógica para posiciones largas

### 1. Elegir base de stop
`B0` toma:
- `B1` si `FirstLowOrMore = 1`
- `min(B1, B2)` si `= 2`
- `min(B1, B2, B3)` si `>= 3`

### 2. Construir stop candidato
`stlong = B0 - space`

Clamp defensivo:
- si `stlong > close` o `stlong < 0.01`, entonces `stlong = close - abs(space)`

### 3. Regla monotónica
Si la barra previa ya estaba larga y el nuevo stop sería más bajo que el anterior, no se mueve.

También se congela si `WaitForXtrem > 0` y el máximo actual todavía no supera `HH0[1]`.

En resumen:
- el stop largo solo puede subir o quedarse igual;
- nunca puede bajar mientras siga vigente la misma secuencia larga.

### 4. Publicación
Si `MarketPosition() = 1`, envía `SetStopPrice(stoplong)`.

## Lógica para posiciones cortas

### 1. Elegir base de stop
`H0` toma:
- `H1` si `FirstHighOrMore = 1`
- `max(H1, H2)` si `= 2`
- `max(H1, H2, H3)` si `>= 3`

### 2. Construir stop candidato
En el fuente original se reutiliza `stlong` como variable auxiliar, pero la lógica funcional es:
`stshort = H0 + space`

Clamp defensivo:
- si `stshort < close`, entonces `stshort = close + abs(space)`

### 3. Regla monotónica
Si la barra previa ya estaba corta y el nuevo stop sería más alto que el anterior, no se mueve.

También se congela si `WaitForXtrem > 0` y el mínimo actual todavía no rompe `BB0[1]`.

En resumen:
- el stop corto solo puede bajar o quedarse igual;
- nunca puede subir mientras siga vigente la misma secuencia corta.

### 4. Publicación
Si `MarketPosition() = -1`, envía `SetStopPrice(stoplong)` en la versión base, reutilizando la misma serie como stop activo.

## Lógica de `WaitForXtrem`
Si `WaitForXtrem > 0`, el indicador almacena un extremo de validación adicional:
- para largos, `HH0` es el máximo entre `H1`, `H2`, `H3` según el valor configurado;
- para cortos, `BB0` es el mínimo entre `B1`, `B2`, `B3` según el valor configurado.

El stop no avanza hasta que precio rompa ese extremo. Esto evita apretar el stop antes de que el mercado confirme un nuevo swing en la dirección favorable.

## Cambio de estado implícito
No existe una máquina de estados explícita, pero sí estas transiciones:
- `flat -> long`: `flaglong` pasa a `1`, se empieza a calcular stop largo.
- `flat -> short`: `flaglong` pasa a `-1`, se empieza a calcular stop corto.
- `long -> long`: el stop solo se ajusta si mejora o si se libera la espera de extremo.
- `short -> short`: igual criterio, pero simétrico.
- al salir a flat, el código no reinicializa agresivamente las memorias históricas; la siguiente posición reutiliza el contexto disponible.

## Lógica barra a barra
1. Al cierre de barra, recalcula la serie `tr` completa y las dos ATR simples.
2. Calcula `space`.
3. Recorre la historia para detectar pivots confirmados y actualizar `H1..H3`, `B1..B3`.
4. Lee `MarketPosition()` y actualiza `flaglong`.
5. Si hay espera de extremo, prepara `HH0` o `BB0`.
6. Si la posición es larga, genera stop largo con base en bajos recientes.
7. Si la posición es corta, genera stop corto con base en altos recientes.
8. Aplica la regla de no alejar el stop.
9. Publica el precio stop correspondiente.

## Relación con `EL_Stop_Intel_v2_live`
La variante live mantiene la misma estructura base, pero añade dos ajustes relevantes:
- una serie `meta(metasentimentor.main)` para corregir el stop de entrada en modo live/open-next-bar;
- separación explícita entre `stcourt` y `stopcourt` para el lado corto.

Para esta spec canónica, la referencia sigue siendo la lógica de `EL_Stop_Intelligent`; la variante live se considera una corrección operacional, no una familia nueva.

## Núcleo funcional vs elementos visuales/accesorios
Núcleo funcional del componente:
- cálculo de `tr`, `avtr`, `avtrref` y `space`
- detección retrospectiva de pivots
- almacenamiento de `H1..H3` y `B1..B3`
- construcción de `B0`, `H0`, `HH0`, `BB0`
- cálculo del stop largo y corto
- regla monotónica de no alejar stop
- congelación opcional por `WaitForXtrem`

Elementos de publicación o accesorios:
- `SetStopPrice(...)` como efecto de plataforma
- diferencias operativas de la variante live
- cualquier futura separación nominal entre stops largos y cortos en la implementación

## Dependencias
- OHLC por barra.
- estado de posición actual.
- acceso a históricos hacia delante y atrás según sintaxis de la plataforma original.
- SMA sobre `tr`.
- motor que acepte actualizar stop por precio absoluto.

## Nota crítica de traducción
La detección de pivots se apoya en confirmación a derecha y en un recorrido retrospectivo. Eso significa que la plataforma original conoce un pivot solo después de varias barras futuras relativas al pivot detectado.

Esto introduce un riesgo claro de traducción:
- una implementación forward-only ingenua puede introducir lookahead indebido,
- o, al contrario, desplazar el pivot y cambiar el nivel efectivo del stop respecto al comportamiento canónico.

Además, `WaitForXtrem` mezcla extremos almacenados con comparación contra la barra actual. Por tanto, la reconstrucción de Fase 2 deberá documentar explícitamente cómo replica:
- la confirmación retrospectiva de pivots,
- la persistencia de `flaglong`,
- y la lógica exacta de congelación/liberación por `HH0` y `BB0`.

## Ambigüedades
Las ambigüedades abiertas se documentan en:
- `mgf-stop-lab/notes/EL_Stop_Intelligent_ambiguities.md`

## Pseudocódigo Python
```python
class StopIntelligent:
    def __init__(
        self,
        quality=2,
        recent_volat=2,
        ref_volat=20,
        coef_volat=5,
        first_low_or_more=2,
        first_high_or_more=2,
        wait_for_xtrem=0,
    ):
        self.quality = quality
        self.recent_volat = recent_volat
        self.ref_volat = ref_volat
        self.coef_volat = coef_volat
        self.first_low_or_more = first_low_or_more
        self.first_high_or_more = first_high_or_more
        self.wait_for_xtrem = wait_for_xtrem

    def true_range(self, high, low, prev_close):
        return max(high - low, abs(prev_close - low), abs(high - prev_close))

    def rolling_sma(self, values, window):
        out = [None] * len(values)
        for i in range(len(values)):
            if i + 1 >= window and all(v is not None for v in values[i - window + 1 : i + 1]):
                sample = values[i - window + 1 : i + 1]
                out[i] = sum(sample) / window
        return out

    def detect_pivots(self, high, low):
        n = len(high)
        haut = [0] * n
        bas = [0] * n
        H1 = [None] * n
        H2 = [None] * n
        H3 = [None] * n
        B1 = [None] * n
        B2 = [None] * n
        B3 = [None] * n

        for i in range(n - 1, -1, -1):
            next_i = i + 1

            H1[i] = H1[next_i] if next_i < n else None
            H2[i] = H2[next_i] if next_i < n else None
            H3[i] = H3[next_i] if next_i < n else None
            B1[i] = B1[next_i] if next_i < n else None
            B2[i] = B2[next_i] if next_i < n else None
            B3[i] = B3[next_i] if next_i < n else None

            if self.quality == 1:
                if i + 3 < n and (
                    ((high[i] < high[i + 1]) and (high[i + 1] > high[i + 2]))
                    or (
                        (high[i] < high[i + 1])
                        and (high[i + 1] >= high[i + 2])
                        and (high[i + 2] > high[i + 3])
                    )
                ):
                    haut[i] = 1

                if i + 3 < n and (
                    ((low[i] > low[i + 1]) and (low[i + 1] < low[i + 2]))
                    or (
                        (low[i] > low[i + 1])
                        and (low[i + 1] <= low[i + 2])
                        and (low[i + 2] < low[i + 3])
                    )
                ):
                    bas[i] = 1

            elif self.quality == 2:
                if i + 4 < n and (
                    high[i] < high[i + 2]
                    and high[i + 1] < high[i + 2]
                    and high[i + 3] <= high[i + 2]
                    and high[i + 2] > high[i + 4]
                ):
                    haut[i] = 2

                if i + 4 < n and (
                    low[i] > low[i + 2]
                    and low[i + 1] > low[i + 2]
                    and low[i + 3] >= low[i + 2]
                    and low[i + 4] >= low[i + 2]
                ):
                    bas[i] = 2

            else:
                if i + 6 < n and (
                    high[i] < high[i + 3]
                    and high[i + 1] < high[i + 3]
                    and high[i + 2] <= high[i + 3]
                    and high[i + 3] >= high[i + 4]
                    and high[i + 3] >= high[i + 5]
                    and high[i + 3] >= high[i + 6]
                ):
                    haut[i] = 3

                if i + 6 < n and (
                    low[i] > low[i + 3]
                    and low[i + 1] > low[i + 3]
                    and low[i + 2] >= low[i + 3]
                    and low[i + 3] <= low[i + 4]
                    and low[i + 3] <= low[i + 5]
                    and low[i + 3] <= low[i + 6]
                ):
                    bas[i] = 3

            if haut[i] > 0 and i + self.quality < n:
                H3[i] = H2[next_i] if next_i < n else None
                H2[i] = H1[next_i] if next_i < n else None
                H1[i] = high[i + self.quality]

            if bas[i] > 0 and i + self.quality < n:
                B3[i] = B2[next_i] if next_i < n else None
                B2[i] = B1[next_i] if next_i < n else None
                B1[i] = low[i + self.quality]

        return H1, H2, H3, B1, B2, B3

    def build_wait_extremes(self, H1, H2, H3, B1, B2, B3, i):
        highs = [v for v in [H1[i], H2[i], H3[i]] if v is not None]
        lows = [v for v in [B1[i], B2[i], B3[i]] if v is not None]

        HH0 = max(highs[: self.wait_for_xtrem]) if highs and self.wait_for_xtrem > 0 else None
        BB0 = min(lows[: self.wait_for_xtrem]) if lows and self.wait_for_xtrem > 0 else None
        return HH0, BB0

    def compute(self, high, low, close, market_position):
        n = len(close)
        tr = [None] * n
        for i in range(n - 1):
            tr[i] = self.true_range(high[i], low[i], close[i + 1])

        avtr = self.rolling_sma(tr, self.recent_volat)
        avtrref = self.rolling_sma(tr, self.ref_volat)
        space = [
            None
            if avtr[i] is None or avtrref[i] is None
            else (((2 * avtrref[i]) - avtr[i]) * self.coef_volat) / 5.0
            for i in range(n)
        ]

        H1, H2, H3, B1, B2, B3 = self.detect_pivots(high, low)
        stop = [None] * n
        flag = [0] * n
        HH0 = [None] * n
        BB0 = [None] * n

        for i in range(n):
            if market_position[i] == 1:
                flag[i] = 1
            elif market_position[i] == -1:
                flag[i] = -1
            elif i > 0:
                flag[i] = flag[i - 1]

            HH0[i], BB0[i] = self.build_wait_extremes(H1, H2, H3, B1, B2, B3, i)

            if space[i] is None:
                continue

            if flag[i] == 1:
                lows = [v for v in [B1[i], B2[i], B3[i]] if v is not None]
                lows = lows[: self.first_low_or_more]
                if not lows:
                    continue

                candidate = min(lows) - space[i]
                if candidate > close[i] or candidate < 0.01:
                    candidate = close[i] - abs(space[i])

                if i > 0 and flag[i - 1] == 1 and stop[i - 1] is not None:
                    if self.wait_for_xtrem > 0 and HH0[i - 1] is not None and high[i] <= HH0[i - 1]:
                        stop[i] = stop[i - 1]
                    elif candidate < stop[i - 1]:
                        stop[i] = stop[i - 1]
                    else:
                        stop[i] = candidate
                else:
                    stop[i] = candidate

            elif flag[i] == -1:
                highs = [v for v in [H1[i], H2[i], H3[i]] if v is not None]
                highs = highs[: self.first_high_or_more]
                if not highs:
                    continue

                candidate = max(highs) + space[i]
                if candidate < close[i]:
                    candidate = close[i] + abs(space[i])

                if i > 0 and flag[i - 1] == -1 and stop[i - 1] is not None:
                    if self.wait_for_xtrem > 0 and BB0[i - 1] is not None and low[i] >= BB0[i - 1]:
                        stop[i] = stop[i - 1]
                    elif candidate > stop[i - 1]:
                        stop[i] = stop[i - 1]
                    else:
                        stop[i] = candidate
                else:
                    stop[i] = candidate

        return {
            "stop": stop,
            "space": space,
            "avtr": avtr,
            "avtrref": avtrref,
            "H1": H1,
            "H2": H2,
            "H3": H3,
            "B1": B1,
            "B2": B2,
            "B3": B3,
            "HH0": HH0,
            "BB0": BB0,
        }
```

## Notas de implementación futura
- La reconstrucción Python deberá decidir cómo mapear el recorrido retrospectivo de pivots a un cálculo cronológico reproducible.
- `WaitForXtrem` necesita pruebas unitarias específicas porque mezcla pivots almacenados con comparación frente a la barra actual.
- La variante live sugiere que el fuente base puede diferir en entrada real respecto a backtest cerrado a fin de barra.
