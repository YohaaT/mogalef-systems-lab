# EL_REPULSE_DIV

## Propósito
Detectar divergencias alcistas y bajistas entre el precio y tres curvas Repulse calculadas localmente, de corto, medio y largo plazo. El componente combina divergencias detectadas sobre tres horizontes (`R1`, `R2`, `R3`) y las traduce a una señal discreta final de compra o venta durante una duración configurable.

No es un sistema completo. Es un motor de entrada por divergencia multi-horizonte.

## Contexto en catálogo
- canonical_name: `EL_REPULSE_DIV`
- family: `mgf-divergence-lab`
- subfamily: `repulse`
- role: `signal`
- priority: `p0_core`
- status previo en catálogo: `classified`

## Inputs

### Parámetros declarados
- `$R1` (default 1): longitud del Repulse corto.
- `$R2` (default 5): longitud del Repulse medio.
- `$R3` (default 15): longitud del Repulse largo.
- `$smoothHighRep1` / `$smoothLowRep1`: suavizados para pivots altos y bajos del Repulse corto.
- `$SmoothHighRep5` / `$SmoothLowRep5`: suavizados para pivots del Repulse medio.
- `$SmoothHighRep15` / `$smoothLowRep15`: suavizados para pivots del Repulse largo.
- `$Activ_R1`, `$Activ_R5`, `$Activ_R15`: activación independiente de cada horizonte.
- `$DecalEntry` (default 0): desplazamiento temporal respecto a la barra de divergencia.
- `$DureeSignal` (default 1): número de barras durante las que una divergencia previa puede activar la señal.
- `$Visualise`: activa resaltado visual.

### Series de entrada de mercado
- `open`
- `high`
- `low`
- `close`
- `date`
- `TickSize()`

## Outputs

### Núcleo funcional
- `INDICM`: Repulse corto, asociado a `$R1`.
- `INDICA`: Repulse medio, asociado a `$R2`.
- `INDICB`: Repulse largo, asociado a `$R3`.
- `DIVHM`: divergencia alcista de corto plazo, valor bruto `0.4`.
- `DIVBM`: divergencia bajista de corto plazo, valor bruto `-0.4`.
- `DIVHA`: divergencia alcista de medio plazo, valor bruto `0.8`.
- `DIVBA`: divergencia bajista de medio plazo, valor bruto `-0.8`.
- `DIVHB`: divergencia alcista de largo plazo, valor bruto `1`.
- `DIVBB`: divergencia bajista de largo plazo, valor bruto `-1`.
- `Pose`: señal discreta agregada.
  - `1`: compra
  - `-1`: venta
- `sentiment`
  - `100`: compra
  - `0`: venta

### Elementos visuales y accesorios
- `ZBM`, `ZHM`: rectas de divergencia para horizonte corto.
- `ZBA`, `ZHA`: rectas de divergencia para horizonte medio.
- `ZBB`, `ZHB`: rectas de divergencia para horizonte largo.
- reescalado visual de las series `DIV*` con `TickSize()`.
- resaltados visuales opcionales.

## Series internas

### Construcción de Repulse
Para cada una de las tres longitudes:
- `bas`, `bas2`, `bas3`: lowest low rolling.
- `haut`, `haut2`, `haut3`: highest high rolling.
- `PousH`, `PousHH`, `PousHHH`: presión alcista previa al suavizado.
- `PousB`, `PousBB`, `PousBBB`: presión bajista previa al suavizado.
- `PousH1`, `PousH2`, `PousH3`: EMA de presión alcista.
- `PousB1`, `PousB2`, `PousB3`: EMA de presión bajista.
- `Length1`, `Length2`, `Length3`: copias de `$R1`, `$R2`, `$R3`.

### Detección de pivots y divergencias
Para cada horizonte se repite el mismo bloque con sufijos:
- `DH*`, `DCH*`: último pivot alto confirmado del indicador y del precio.
- `AH*`, `ACH*`: pivot alto actual candidato y precio asociado.
- `DB*`, `DCB*`: último pivot bajo confirmado.
- `AB*`, `ACB*`: pivot bajo actual candidato.
- `compteurB*`, `compteurH*`: distancia en barras entre pivots.
- `temp1*..temp6*`: máximos, mínimos y auxiliares.
- `a`, `b`: parámetros de recta para dibujar divergencias.

## Cálculo de las tres curvas Repulse
El código no llama un Repulse externo. Lo reconstruye localmente para tres longitudes.

### Paso 1, rango rolling
Para cada longitud `L`:
- `lowest_low_L = min(low de las últimas L barras)`
- `highest_high_L = max(high de las últimas L barras)`

### Paso 2, presión alcista y bajista
Para cada barra:
- `bull_push = ((3*close) - (2*lowest_low_L) - open[L-1]) * 100 / close`
- `bear_push = (open[L-1] - (3*close) + (2*highest_high_L)) * 100 / close`

### Paso 3, suavizado exponencial
Cada presión se suaviza con EMA de periodo `L*5`.

### Paso 4, repulse final
- `repulse_L = ema_bull_push - ema_bear_push`

Asignación por horizonte:
- `INDICM = repulse de R1`
- `INDICA = repulse de R2`
- `INDICB = repulse de R3`

## Detección de divergencias por horizonte
La lógica se repite tres veces, una por cada curva Repulse.

### Pivot alto previo confirmado
Para un horizonte con suavizado `smooth_high`:
- `temp1 = Highest(indic, smooth_high + 1)`
- `temp2 = temp1[smooth_high]`

Si `indic[smooth_high]` coincide con ambos valores, se confirma un pivot alto previo:
- `DH = indic[smooth_high]`
- `DCH = Highest(high, (2*smooth_high)+1)`
- `compteurB = smooth_high`

Si no, se conserva el pivot anterior y aumenta `compteurB`.

Caso especial si `smooth_high <= 1`:
- usa una comparación fija sobre `indic[3]`, `temp1[2]`, `temp1[3]` y `Highest(high,3)`.

### Pivot alto actual candidato
Se activa si:
- `close <= close[1]`
- `indic < indic[1]`
- `indic[1] = temp1[1]`

Entonces:
- `AH = indic[1]`
- `ACH = Highest(high, smooth_high + 2)`

### Divergencia bajista
Condiciones:
- `AH <> AH[1]`
- `DH > AH` (máximo descendente del indicador)
- `DCH < ACH` (máximo ascendente del precio)
- horizonte activado

Entonces se marca una divergencia bajista con amplitud específica del horizonte:
- corto: `DIVBM = -0.4`
- medio: `DIVBA = -0.8`
- largo: `DIVBB = -1`

### Pivot bajo previo confirmado
Con lógica espejo usando `Lowest` y el suavizado bajo.

Si se confirma:
- `DB = indic[smooth_low]`
- `DCB = Lowest(low, (2*smooth_low)+1)`
- `compteurH = smooth_low`

### Pivot bajo actual candidato
Se activa si:
- `close >= close[1]`
- `indic > indic[1]`
- `indic[1] = temp4[1]`

Entonces:
- `AB = indic[1]`
- `ACB = Lowest(low, smooth_low + 2)`

### Divergencia alcista
Condiciones:
- `AB <> AB[1]`
- `DB < AB` (mínimo ascendente del indicador)
- `DCB > ACB` (mínimo descendente del precio)
- horizonte activado

Entonces:
- corto: `DIVHM = 0.4`
- medio: `DIVHA = 0.8`
- largo: `DIVHB = 1`

## Líneas de divergencia
Cuando hay divergencia en un horizonte, se dibuja una recta entre el pivot actual y el previo del indicador:
- `a = pivot actual`
- `b = (pivot previo - pivot actual) / (distancia - 1)`
- para `i = 1 .. distancia`, `Z*[i] = a + b*(i-1)`

Luego la serie visible en barra actual se pone `void`, dejando solo el tramo histórico.

## Agregación de señal final
El componente no decide por prioridad conceptual, sino por orden de código.

Para `i = 1 .. $DureeSignal`:
- si `Pose` todavía no es `1` ni `-1`, revisa divergencias desplazadas por `$DecalEntry + i - 1`
- en este orden:
  1. `DIVHM` corto alcista
  2. `DIVBM` corto bajista
  3. `DIVHA` medio alcista
  4. `DIVBA` medio bajista
  5. `DIVHB` largo alcista
  6. `DIVBB` largo bajista

Si encuentra una divergencia alcista activa y el horizonte está habilitado:
- `Pose = 1`

Si encuentra una divergencia bajista activa y el horizonte está habilitado:
- `Pose = -1`

Como la comprobación es secuencial, la primera coincidencia útil dentro del bloque puede decidir la señal final.

## Reescalado visual de divergencias
Antes del bloque `interpretation`, las divergencias se reescalan con `TickSize()`:
- `DIVHM`, `DIVBM` multiplicadas por `TickSize()/5`
- `DIVHA`, `DIVBA` multiplicadas por `TickSize()/4`
- `DIVHB`, `DIVBB` multiplicadas por `TickSize()/3`

Esto parece orientado a visibilidad en plot, no a cambiar la lógica de señal ya decidida.

## Lógica de cambio de estado
Estados implícitos:

### Estado neutro
- no hay divergencias activas en la ventana revisada por `$DureeSignal`
- `Pose` permanece sin cambio útil

### Estado compra
- aparece una divergencia alcista habilitada en alguno de los tres horizontes dentro de la ventana revisada
- `Pose = 1`
- `sentiment = 100`

### Estado venta
- aparece una divergencia bajista habilitada dentro de la ventana revisada
- `Pose = -1`
- `sentiment = 0`

## Núcleo funcional vs elementos visuales/accesorios
Núcleo funcional del componente:
- construcción de `INDICM`, `INDICA`, `INDICB`
- detección de pivots por horizonte
- detección de divergencias alcistas y bajistas
- agregación final en `Pose`
- traducción a `sentiment`

Elementos visuales y accesorios:
- rectas `Z*`
- reescalado de `DIV*` para plot
- resaltados visuales
- cualquier diferencia de plotting por `TickSize()`

## Lógica barra a barra
1. En la primera barra, desactiva cálculo por tick.
2. Calcula tres curvas Repulse autónomas para longitudes `$R1`, `$R2`, `$R3`.
3. Para cada curva, detecta pivots altos y bajos del indicador.
4. Compara esos pivots con pivots de precio para detectar divergencias alcistas y bajistas.
5. Dibuja rectas de divergencia cuando aparecen.
6. Recorre una ventana de hasta `$DureeSignal` barras desplazadas por `$DecalEntry`.
7. Si encuentra una divergencia habilitada, asigna `Pose`.
8. Reescala los marcadores de divergencia para plot.
9. En `interpretation`, traduce `Pose` a `sentiment`.

## Dependencias
- OHLC por barra.
- acceso a histórico suficiente para `open[L-1]` y rangos rolling.
- `Highest`, `Lowest`, `ExpMovingAverage`, `IsFirstBar`, `FinalBarIndex`, `TickSize`.
- motor gráfico para `plot` y `Highlight`.

## Nota crítica de traducción
La fuente usa indexing retrospectivo y una semántica de series persistentes que no se traslada automáticamente a Python:
- el acceso a `open[L-1]` en bucles retrospectivos debe mapearse con precisión,
- la confirmación de pivots depende de comparaciones sobre barras futuras relativas al pivot,
- y `Pose` parece comportarse como serie persistente del host, no como variable local reinicializada en cada barra.

Eso introduce un riesgo real de lookahead o de desplazamiento temporal si la traducción se hace de forma ingenua.

La reconstrucción de Fase 2 deberá documentar explícitamente:
- cómo se mapea `open[L-1]` al eje cronológico normal,
- cómo se confirma cada pivot sin alterar la barra efectiva de la divergencia,
- y cómo se reinicializa o persiste `Pose` para no cambiar la duración real de la señal.

## Ambigüedades
Las ambigüedades abiertas se documentan en:
- `mgf-divergence-lab/notes/EL_REPULSE_DIV_ambiguities.md`

## Pseudocódigo Python
El siguiente pseudocódigo es **estructural**. Sirve para fijar módulos y orden de cálculo, pero no pretende cerrar todavía todos los detalles finos de persistencia retrospectiva del host original.

```python
def repulse_series(open_, high, low, close, length):
    lowest = rolling_min(low, length)
    highest = rolling_max(high, length)

    bull = [None] * len(close)
    bear = [None] * len(close)

    for i in range(len(close)):
        src = i - (length - 1)
        if src < 0 or lowest[i] is None or highest[i] is None or close[i] == 0:
            continue

        bull[i] = ((3 * close[i]) - (2 * lowest[i]) - open_[src]) * 100 / close[i]
        bear[i] = (open_[src] - (3 * close[i]) + (2 * highest[i])) * 100 / close[i]

    ema_bull = ema(bull, length * 5)
    ema_bear = ema(bear, length * 5)

    return [
        None if ema_bull[i] is None or ema_bear[i] is None else ema_bull[i] - ema_bear[i]
        for i in range(len(close))
    ]


def detect_divergences_for_horizon(indic, high, low, close, smooth_high, smooth_low):
    # Pseudocódigo estructural: aquí debe replicarse la lógica retrospectiva
    # de pivots confirmados y pivots actuales candidatos del código original.
    return {
        "bull_div": [0] * len(close),
        "bear_div": [0] * len(close),
        "bull_lines": [None] * len(close),
        "bear_lines": [None] * len(close),
    }


def repulse_div(
    open_,
    high,
    low,
    close,
    r1=1,
    r2=5,
    r3=15,
    activ_r1=True,
    activ_r5=True,
    activ_r15=True,
    decal_entry=0,
    duree_signal=1,
):
    indic_m = repulse_series(open_, high, low, close, r1)
    indic_a = repulse_series(open_, high, low, close, r2)
    indic_b = repulse_series(open_, high, low, close, r3)

    div_m = detect_divergences_for_horizon(indic_m, high, low, close, smooth_high=1, smooth_low=1)
    div_a = detect_divergences_for_horizon(indic_a, high, low, close, smooth_high=3, smooth_low=3)
    div_b = detect_divergences_for_horizon(indic_b, high, low, close, smooth_high=6, smooth_low=6)

    pose = [None] * len(close)

    for idx in range(len(close)):
        chosen = None
        for offset in range(duree_signal):
            j = idx - (decal_entry + offset)
            if j < 0:
                continue

            if chosen is None and activ_r1 and div_m["bull_div"][j] > 0:
                chosen = 1
            if chosen is None and activ_r1 and div_m["bear_div"][j] < 0:
                chosen = -1
            if chosen is None and activ_r5 and div_a["bull_div"][j] > 0:
                chosen = 1
            if chosen is None and activ_r5 and div_a["bear_div"][j] < 0:
                chosen = -1
            if chosen is None and activ_r15 and div_b["bull_div"][j] > 0:
                chosen = 1
            if chosen is None and activ_r15 and div_b["bear_div"][j] < 0:
                chosen = -1

        pose[idx] = chosen

    sentiment = [100 if p == 1 else 0 if p == -1 else None for p in pose]

    return {
        "INDICM": indic_m,
        "INDICA": indic_a,
        "INDICB": indic_b,
        "Pose": pose,
        "sentiment": sentiment,
    }
```

## Notas de implementación futura
- La lógica exacta de `Pose` debe validarse con tests específicos de persistencia.
- El reescalado por `TickSize()` debe mantenerse en la capa visual, no en la lógica de decisión.
- No debe extrapolarse soporte de divergencias inversas desde este componente porque esta variante no las incluye.
