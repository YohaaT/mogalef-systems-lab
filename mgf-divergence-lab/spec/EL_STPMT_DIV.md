# EL_STPMT_DIV

## Propósito
Detectar divergencias alcistas y bajistas entre el precio y una versión interna del oscilador STPMT. El componente genera señales discretas de compra y venta a partir de pivots del indicador comparados con pivots de precio, con opción de incluir divergencias normales, inversas o ambas.

No es un sistema completo. Es un motor de señal de divergencia apoyado en una STPMT calculada localmente.

## Contexto en catálogo
- canonical_name: `EL_STPMT_DIV`
- family: `mgf-divergence-lab`
- subfamily: `stpmt`
- role: `signal`
- priority: `p0_core`
- status previo en catálogo: `classified`

## Inputs

### Parámetros declarados
- `$StartTime`: hora mínima para emitir alertas de interpretación.
- `$EndTime`: hora máxima para emitir alertas de interpretación.
- `$MessageBox`: activa popup de alerta.
- `$PlaySound`: activa sonido.
- `$SendEmail`: activa email.
- `$SmoothH` (default 2): suavizado usado para detectar pivots altos del indicador.
- `$SmoothB` (default 2): suavizado usado para detectar pivots bajos del indicador.
- `$ONone1Normals2Inverses3All` (default 1): selector del tipo de divergencia.
  - 0: ninguna
  - 1: normales
  - 2: inversas
  - 3: ambas
- `$decalentry` (default 0): desplazamiento de entrada respecto a la barra donde aparece la divergencia.
- `$DistanceMaxH` (default 200): distancia máxima permitida entre pivots altos para divergencia bajista.
- `$DistancemaxL` (default 200): distancia máxima permitida entre pivots bajos para divergencia alcista.
- `$Visualise`: activa resaltado visual.

### Series de entrada de mercado
- `open`
- `high`
- `low`
- `close`
- `timeopen`
- `date`

## Outputs

### Núcleo funcional
- `INDIC`: copia de `STPMTe`, el oscilador STPMT compuesto.
- `DIVH`: divergencia alcista normal, valor `3`.
- `DIVB`: divergencia bajista normal, valor `-3`.
- `DIVHI`: divergencia alcista inversa, valor `2`.
- `DIVBI`: divergencia bajista inversa, valor `-2`.
- `pose`: decisión final de señal.
- `sentiment`: 100 compra, 0 venta.

### Elementos visuales y accesorios
- `ZB`: línea entre pivots de divergencia alcista normal.
- `ZH`: línea entre pivots de divergencia bajista normal.
- `ZBI`: línea entre pivots de divergencia alcista inversa.
- `ZHI`: línea entre pivots de divergencia bajista inversa.
- `Stod1`, `Stod2`, `Stod3`, `Stod4`: suavizados visibles de los cuatro estocásticos base.
- `MA`: media móvil visible de `STPMTe`.
- `k=40`, `kk=52`: referencias horizontales constantes.
- alertas visuales, sonoras, email y popup.

## Series internas

### Construcción STPMT
- `PH1/PB1`, `PH2/PB2`, `PH3/PB3`, `PH4/PB4`: máximos y mínimos rolling de 5, 14, 45 y 75 barras.
- `NumK1..4`, `DenoK1..4`: numeradores y denominadores de los cuatro `%K`.
- `StoK1..4`: `%K` de cada ventana.
- `Stod1..4`: medias móviles de `StoK1..4` con ventanas 3, 3, 14 y 20.
- `STPMTe`: mezcla ponderada de los cuatro `Stod`.
- `MA`: media móvil de `STPMTe` con ventana 9.

### Detección de pivots y divergencias
- `DH`, `DCH`: último pivot alto confirmado de indicador y precio asociado.
- `AH`, `ACH`: pivot alto actual candidato de indicador y precio asociado.
- `DB`, `DCB`: último pivot bajo confirmado de indicador y precio asociado.
- `AB`, `ACB`: pivot bajo actual candidato de indicador y precio asociado.
- `compteurB`, `compteurH`: distancia en barras entre pivots altos o bajos.
- `temp1..6`: máximos, mínimos y auxiliares de confirmación.
- `a`, `b`: coeficientes para dibujar rectas de divergencia.

## Construcción del oscilador STPMT
El componente no llama un indicador externo. Reconstruye una STPMT local a partir de cuatro estocásticos sobre `close` usando ventanas de máximos y mínimos de precio.

### Ventanas usadas
- 5 barras
- 14 barras
- 45 barras
- 75 barras

### Fórmula base por ventana
Para cada ventana:
- `PHn`: máximo del `high` en la ventana
- `PBn`: mínimo del `low` en la ventana
- `NumKn = PHn - close`
- `DenoKn = PHn - PBn`

Si `DenoKn = 0`, entonces `StoKn = 100`.
Si no:
- `StoKn = 100 - ((NumKn / DenoKn) * 100)`

Es equivalente a un estocástico `%K` clásico expresado como posición del cierre dentro del rango high-low.

### Suavizados
- `Stod1 = MA(StoK1, 3)`
- `Stod2 = MA(StoK2, 3)`
- `Stod3 = MA(StoK3, 14)`
- `Stod4 = MA(StoK4, 20)`

### Composición final
`STPMTe = ((4.1*Stod1) + (2.5*Stod2) + Stod3 + (4*Stod4)) / 11.6`

Luego:
- `INDIC = STPMTe`
- `MA = MovingAverage(STPMTe, 9)`

## Detección de pivots del indicador

### Pivot alto previo confirmado
Se busca un máximo local del indicador usando `$SmoothH`.

Caso general (`$SmoothH > 1`):
- `temp1 = Highest(INDIC, $SmoothH + 1)`
- `temp2 = temp1[$SmoothH]`
- si `INDIC[$SmoothH]` coincide con ambos, se confirma un pivot alto previo.

Entonces:
- `DH = INDIC[$SmoothH]`
- `DCH = Highest(high, (2*$SmoothH)+1)`
- `compteurB = $SmoothH`

Si no, el último pivot alto se conserva y `compteurB` incrementa en 1.

Caso especial (`$SmoothH <= 1`):
- usa una comparación fija sobre `INDIC[3]` y `Highest(high,3)` para estabilizar el caso corto.

### Pivot alto actual candidato
Se define cuando:
- el `high` actual no supera los dos previos,
- el indicador cae frente a la barra previa,
- la barra previa fue máximo local del indicador,
- la distancia entre pivots es menor que `$DistanceMaxH`.

Entonces:
- `AH = INDIC[1]`
- `ACH = Highest(high, $SmoothH + 2)`

Si no, se heredan `AH` y `ACH`.

### Pivot bajo previo confirmado
Análogo con `$SmoothB`:
- `temp4 = Lowest(INDIC, $SmoothB + 1)`
- `temp5 = temp4[$SmoothB]`

Si se confirma:
- `DB = INDIC[$SmoothB]`
- `DCB = Lowest(low, (2*$SmoothB)+1)`
- `compteurH = $SmoothB`

Si no, se conserva el pivot previo y `compteurH` aumenta.

Caso especial para `$SmoothB <= 1`:
- usa `INDIC[3]` y `Lowest(low,3)`.

### Pivot bajo actual candidato
Se define cuando:
- el `low` actual no perfora los dos previos,
- el indicador sube frente a la barra previa,
- la barra previa fue mínimo local del indicador,
- la distancia entre pivots es menor que `$DistancemaxL`.

Entonces:
- `AB = INDIC[1]`
- `ACB = Lowest(low, $SmoothB + 2)`

## Lógica de divergencias

### Divergencia bajista normal
Disponible si `$ONone1Normals2Inverses3All = 1` o `3`.

Condiciones:
- `AH <> AH[1]` (nuevo pivot actual)
- `DH > AH` (indicador hace máximo descendente)
- `DCH < ACH` (precio hace máximo ascendente)

Entonces:
- `DIVB = -3`

### Divergencia bajista inversa
Disponible si selector `2` o `3`.

Condiciones:
- `AH <> AH[1]`
- `DH < AH` (indicador hace máximo ascendente)
- `DCH > ACH` (precio hace máximo descendente)

Entonces:
- `DIVBI = -2`

### Divergencia alcista normal
Disponible si selector `1` o `3`.

Condiciones:
- `AB <> AB[1]`
- `DB < AB` (indicador hace mínimo ascendente)
- `DCB > ACB` (precio hace mínimo descendente)

Entonces:
- `DIVH = 3`

### Divergencia alcista inversa
Disponible si selector `2` o `3`.

Condiciones:
- `AB <> AB[1]`
- `DB > AB` (indicador hace mínimo descendente)
- `DCB < ACB` (precio hace mínimo ascendente)

Entonces:
- `DIVHI = 2`

## Líneas de divergencia
Cuando aparece una divergencia, el indicador dibuja una recta entre el pivot actual y el pivot previo del oscilador.

Para cada tipo:
- `a = pivot actual`
- `b = (pivot previo - pivot actual) / (distancia - 1)`
- para `i = 1 .. distancia`, se asigna `Z*[i] = a + b*(i-1)`

Después la propia serie se vuelve `void` en la barra actual, dejando visible solo el tramo retrospectivo.

## Lógica de cambio de estado
No existe una máquina de estados explícita, pero sí estados implícitos:

### Estado neutro
- no hay divergencia detectada
- `pose` conserva su último valor o permanece vacío

### Estado compra
Se activa si `DIVH[$decalentry] > 0` o `DIVHI[$decalentry] > 0`.
- `pose = 1`
- `sentiment = 100`

### Estado venta
Se activa si `DIVB[$decalentry] < 0` o `DIVBI[$decalentry] < 0`.
- `pose = -1`
- `sentiment = 0`

La prioridad real depende del orden secuencial del código. Si en la misma barra aparecen señales opuestas, la última asignación ejecutada puede sobrescribir la anterior.

## Núcleo funcional vs elementos visuales/accesorios
Núcleo funcional del componente:
- construcción de `STPMTe`
- detección de pivots altos y bajos
- detección de divergencias normales e inversas
- asignación de `pose`
- traducción final a `sentiment`

Elementos visuales y accesorios:
- líneas `Z*`
- plots de `Stod1..4`, `MA`, `k`, `kk`
- resaltado visual y alertas (`MessageBox`, `PlaySound`, `SendEmail`)
- filtro horario aplicado en la capa de interpretación

## Lógica barra a barra
1. En la primera barra, desactiva cálculo por tick.
2. Recorre todo el histórico para construir máximos y mínimos rolling de 4 ventanas.
3. Calcula los cuatro `StoK`.
4. Suaviza cada uno y compone `STPMTe`.
5. Copia `STPMTe` en `INDIC`.
6. En cada barra corriente, detecta el último pivot alto y bajo confirmados del oscilador.
7. Detecta pivots actuales candidatos del oscilador y asocia máximos/mínimos de precio.
8. Evalúa divergencias normales e inversas según el selector.
9. Si hay divergencia en la barra desplazada por `$decalentry`, asigna `pose`.
10. En interpretación, si la barra está completada y dentro del horario, traduce `pose` a `sentiment` y alertas opcionales.

## Dependencias
- OHLC por barra.
- acceso a históricos negativos y positivos según la sintaxis del motor.
- funciones `Highest`, `Lowest`, `MovingAverage`, `IsFirstBar`, `IsBarCompleted`, `FinalBarIndex`.
- sistema de alertas opcional del host.

## Nota crítica de traducción
La construcción de la STPMT y de los pivots usa bucles retrospectivos e índices negativos de la plataforma original. Eso introduce un riesgo real de porting:
- una implementación forward-only ingenua puede desplazar los primeros valores válidos,
- puede alterar el momento exacto en que se confirma un pivot,
- y puede introducir o eliminar lookahead accidental si no se replica bien la semántica del host.

Además, la señal interna y la capa de interpretación no son idénticas:
- la divergencia se calcula independientemente del horario,
- pero el horario y las alertas solo afectan la capa de interpretación.

Por tanto, la reconstrucción posterior deberá documentar explícitamente:
- cómo se reconstruyen `PH*`, `PB*`, `StoK*`, `Stod*` y `STPMTe` sin desfases,
- cómo se confirma un pivot sin alterar la barra efectiva de señal,
- y cómo se separa la señal funcional de la capa de alertas/visualización.

## Ambigüedades
Las ambigüedades abiertas se documentan en:
- `mgf-divergence-lab/notes/EL_STPMT_DIV_ambiguities.md`

## Pseudocódigo Python
El siguiente pseudocódigo es **estructural**, no ejecutable de forma directa. Su objetivo es fijar el orden lógico de cálculo y las dependencias principales sin ocultar que la traducción exacta de pivots retrospectivos requiere una implementación cuidada.

```python
def build_stpmte(high, low, close):
    ph1, pb1 = rolling_high_low(high, low, 5)
    ph2, pb2 = rolling_high_low(high, low, 14)
    ph3, pb3 = rolling_high_low(high, low, 45)
    ph4, pb4 = rolling_high_low(high, low, 75)

    stok1 = stochastic_from_range(close, ph1, pb1)
    stok2 = stochastic_from_range(close, ph2, pb2)
    stok3 = stochastic_from_range(close, ph3, pb3)
    stok4 = stochastic_from_range(close, ph4, pb4)

    stod1 = moving_average(stok1, 3)
    stod2 = moving_average(stok2, 3)
    stod3 = moving_average(stok3, 14)
    stod4 = moving_average(stok4, 20)

    stpmte = [
        None
        if any(v is None for v in [stod1[i], stod2[i], stod3[i], stod4[i]])
        else ((4.1 * stod1[i]) + (2.5 * stod2[i]) + stod3[i] + (4 * stod4[i])) / 11.6
        for i in range(len(close))
    ]

    ma = moving_average(stpmte, 9)
    return stpmte, ma, stod1, stod2, stod3, stod4


def stpmt_div(
    high,
    low,
    close,
    smooth_h=2,
    smooth_b=2,
    mode=1,
    decal_entry=0,
    dist_max_h=200,
    dist_max_l=200,
):
    indic, ma, stod1, stod2, stod3, stod4 = build_stpmte(high, low, close)

    divh = [0] * len(close)
    divb = [0] * len(close)
    divhi = [0] * len(close)
    divbi = [0] * len(close)
    pose = [None] * len(close)

    high_state = init_high_pivot_state()
    low_state = init_low_pivot_state()

    for i in range(len(close)):
        high_state = update_last_high_pivot(indic, high, i, smooth_h, high_state)
        high_state = update_current_high_candidate(indic, high, i, smooth_h, dist_max_h, high_state)

        low_state = update_last_low_pivot(indic, low, i, smooth_b, low_state)
        low_state = update_current_low_candidate(indic, low, i, smooth_b, dist_max_l, low_state)

        if mode in (1, 3) and is_new_high_candidate(high_state):
            if high_state.last_indicator_high > high_state.current_indicator_high and high_state.last_price_high < high_state.current_price_high:
                divb[i] = -3

        if mode in (2, 3) and is_new_high_candidate(high_state):
            if high_state.last_indicator_high < high_state.current_indicator_high and high_state.last_price_high > high_state.current_price_high:
                divbi[i] = -2

        if mode in (1, 3) and is_new_low_candidate(low_state):
            if low_state.last_indicator_low < low_state.current_indicator_low and low_state.last_price_low > low_state.current_price_low:
                divh[i] = 3

        if mode in (2, 3) and is_new_low_candidate(low_state):
            if low_state.last_indicator_low > low_state.current_indicator_low and low_state.last_price_low < low_state.current_price_low:
                divhi[i] = 2

        src = i - decal_entry
        if src >= 0:
            if divh[src] > 0 or divhi[src] > 0:
                pose[i] = 1
            if divb[src] < 0 or divbi[src] < 0:
                pose[i] = -1

    sentiment = [100 if p == 1 else 0 if p == -1 else None for p in pose]

    return {
        "INDIC": indic,
        "MA": ma,
        "Stod1": stod1,
        "Stod2": stod2,
        "Stod3": stod3,
        "Stod4": stod4,
        "DIVH": divh,
        "DIVB": divb,
        "DIVHI": divhi,
        "DIVBI": divbi,
        "pose": pose,
        "sentiment": sentiment,
    }
```

## Notas de implementación futura
- La reconstrucción debe fijar con precisión la equivalencia de `MovingAverage` y el tratamiento de primeras barras.
- El orden exacto de confirmación de pivots debe testearse con casos controlados para evitar desfases.
- Los overlays `k` y `kk` deben tratarse como visuales, no como lógica de señal.
