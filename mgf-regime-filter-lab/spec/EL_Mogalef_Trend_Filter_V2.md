# EL_Mogalef_Trend_Filter_V2

## Propósito
Clasificar cada barra en uno de ocho casos de régimen según la dirección de tres repulses de distinta escala (`R1`, `R2`, `R3`) y, a partir de esa clasificación, bloquear o dejar pasar operaciones. No genera entrada por sí mismo. Es un filtro de contexto.

## Contexto en catálogo
- canonical_name: `EL_Mogalef_Trend_Filter_V2`
- family: `mgf-regime-filter-lab`
- subfamily: `trend-overlays`
- role: `filter`
- priority: `p0_core`
- status previo en catálogo: `classified`
- variante previa: `EL_Mogalef_Trend_Filter`
- indicador relacionado: `EL_Mogalef_Trend_Indicator`

## Inputs

### Parámetros de control de bloqueo
- `BlockCase1..BlockCase8` (`0/1`): define qué casos se bloquean.
- `TradeOnlyThisCASE` (`0..8`, default `0`): si es distinto de cero, solo deja pasar ese caso exacto y bloquea todos los demás.
- `OffOn` (`0/1`, default `1`): interruptor maestro del filtro.

### Parámetros de repulse
- `R1` (`1..100`, default `1`): horizonte corto.
- `R2` (`50..400`, default `90`): horizonte medio.
- `R3` (`100..800`, default `150`): horizonte largo.

### Series de mercado
- `open`, `high`, `low`, `close`
- índice de barra actual y final
- fecha, usada para una desactivación dura posterior a 2030

## Outputs

### Núcleo funcional
- `CAS`: serie discreta de régimen con valores `1..8` o `void`.

### Capa de interpretación y accesorios
- `sentiment`: `senti_block` o `senti_pass` en la plataforma original.
- `Plot(CAS)`: representación visual del caso activo.

## Series internas
- `INDIC1`, `INDIC5`, `INDIC15`: repulses autónomos para `R1`, `R2`, `R3`.
- `sensR1`, `sensR5`, `sensR15`: dirección de cada repulse, con convención binaria `1` si sube y `-1` si no sube.
- `bas`, `haut`, `bas2`, `haut2`, `bas3`, `haut3`: extremos rolling por horizonte.
- `PousH*`, `PousB*`: componentes alcistas y bajistas antes y después de EMA.

## Concepto de repulse usado en V2
A diferencia de la versión anterior, V2 calcula cada repulse usando extremos recientes de precio.

Para una longitud `L`:
- `lowest_low_L = mínimo(low, ventana L)`
- `highest_high_L = máximo(high, ventana L)`
- `push_up_raw = ((3 * close) - (2 * lowest_low_L) - open_shifted) * 100 / close`
- `push_down_raw = (open_shifted - (3 * close) + (2 * highest_high_L)) * 100 / close`
- `repulse = EMA(push_up_raw, L*5) - EMA(push_down_raw, L*5)`

Donde `open_shifted = open[L-1 barras atrás]` según la sintaxis original.

Interpretación funcional:
- el repulse mejora cuando el cierre actual domina al precio de apertura remoto y además lo hace cerca de máximos de su ventana;
- empeora cuando el cierre actual se acerca al mínimo relativo o queda por debajo del impulso esperado.

## Cálculo de los tres repulses

### Repulse corto
Usa `R1`.

### Repulse medio
Usa `R2`.

### Repulse largo
Usa `R3`.

Los tres siguen exactamente la misma fórmula, solo cambia la longitud.

## Conversión a dirección
Para cada barra:
- si `INDIC1[t] > INDIC1[t-1]`, entonces `sensR1 = 1`, si no `-1`
- si `INDIC5[t] > INDIC5[t-1]`, entonces `sensR5 = 1`, si no `-1`
- si `INDIC15[t] > INDIC15[t-1]`, entonces `sensR15 = 1`, si no `-1`

No existe estado neutro. El empate cae al lado `-1` porque el código usa `else -1`.

## Mapa de casos
El filtro codifica los 8 casos posibles de tres direcciones binarias:

- Caso 8: `sensR15=1`, `sensR5=1`, `sensR1=1`
- Caso 7: `sensR15=1`, `sensR5=1`, `sensR1=-1`
- Caso 6: `sensR15=1`, `sensR5=-1`, `sensR1=1`
- Caso 5: `sensR15=1`, `sensR5=-1`, `sensR1=-1`
- Caso 4: `sensR15=-1`, `sensR5=1`, `sensR1=1`
- Caso 3: `sensR15=-1`, `sensR5=1`, `sensR1=-1`
- Caso 2: `sensR15=-1`, `sensR5=-1`, `sensR1=1`
- Caso 1: `sensR15=-1`, `sensR5=-1`, `sensR1=-1`

La numeración no expresa fuerza lineal, sino combinación binaria de pendiente en tres escalas.

## Reglas de validez del caso
- si `CurrentBarIndex() < (R3 * 5)`, entonces `CAS = void`
- si `date > 05_12_2030`, entonces `CAS = 0`

La primera regla evita clasificar sin suficiente historia para que la EMA larga sea estable.

## Interpretación operativa

### Filtro apagado
Si `OffOn != 1`, el bloque `Interpretation` no fuerza bloqueo. En práctica, el filtro queda inactivo.

### Modo `TradeOnlyThisCASE`
Si `TradeOnlyThisCASE != 0`:
- si `CAS != TradeOnlyThisCASE`, entonces `sentiment = senti_block`
- si `CAS == TradeOnlyThisCASE`, entonces `sentiment = senti_pass`

### Modo por lista de casos bloqueados
Si `TradeOnlyThisCASE == 0`:
- para cada caso `k`, si `BlockCasek != 0` y `CAS == k`, entonces `sentiment = senti_block`
- si no se activa ningún bloqueo, el resultado queda en pass implícito

### Regla de seguridad
Si `CAS = void`, entonces `sentiment = senti_block`.

## Núcleo funcional vs elementos visuales/accesorios
Núcleo funcional del componente:
- construcción de los tres repulses
- derivación de `sensR1`, `sensR5`, `sensR15`
- clasificación de la barra en `CAS`
- aplicación de regla de validez por historia mínima y caducidad por fecha

Capa de interpretación y accesorios:
- traducción de `CAS` a `sentiment`
- política de bloqueo `TradeOnlyThisCASE` o `BlockCase1..8`
- `Plot(CAS)` como visualización

## Lógica barra a barra
1. Solo en `isfirstbar()`, reconstruye toda la historia de los tres repulses.
2. Para cada longitud, calcula rolling low y rolling high retrospectivos.
3. Calcula `push_up_raw` y `push_down_raw` usando cierre actual, extremos recientes y apertura desplazada.
4. Suaviza ambos con EMA de longitud `5 * L`.
5. Obtiene cada repulse como diferencia entre impulso alcista y bajista suavizados.
6. Compara cada repulse contra su barra previa y asigna dirección `1` o `-1`.
7. Convierte la triple combinación de signos en `CAS` de `1` a `8`.
8. Si no hay historia suficiente, marca `CAS = void`.
9. En interpretación, aplica la política de bloqueo configurada.

## Diferencia principal frente a `EL_Mogalef_Trend_Filter`
La versión previa calcula repulse solo con `open` y `close`. V2 añade `lowest low` y `highest high` a la fórmula. Eso vuelve el filtro más sensible a estructura de rango y no solo a desplazamiento neto entre apertura remota y cierre actual.

## Dependencias
- OHLC por barra.
- EMA reproducible.
- rolling low y rolling high para tres longitudes.
- semántica de `void` o equivalente `None/NaN`.
- motor de interpretación con salida bloquea/pasa.

## Nota crítica de traducción
La plataforma original combina dos fuentes de ambigüedad de porting:
- indexing retrospectivo con `[-i]` y aperturas desplazadas del tipo `open[L-1 barras atrás]`,
- y una inicialización implícita del flujo de interpretación que puede depender del host.

Esto implica riesgo real de traducción:
- un desfase de una barra en `open_shifted` cambia los tres repulses,
- una EMA inicializada distinto puede alterar el caso en barras tempranas,
- y la política de `sentiment` cuando `OffOn=0` o cuando no se bloquea ningún caso debe quedar explícita en Fase 2 para evitar arrastre de estado del host original.

La reconstrucción posterior deberá documentar cómo se resuelve cada una de esas decisiones sin alterar la lógica funcional canónica.

## Ambigüedades
Las ambigüedades abiertas se documentan en:
- `mgf-regime-filter-lab/notes/EL_Mogalef_Trend_Filter_V2_ambiguities.md`

## Pseudocódigo Python
```python
class MogalefTrendFilterV2:
    def __init__(
        self,
        r1=1,
        r2=90,
        r3=150,
        trade_only_case=0,
        blocked_cases=None,
        off_on=1,
    ):
        self.r1 = r1
        self.r2 = r2
        self.r3 = r3
        self.trade_only_case = trade_only_case
        self.blocked_cases = set(blocked_cases or [])
        self.off_on = off_on

    def rolling_low(self, values, window):
        out = [None] * len(values)
        for i in range(len(values)):
            if i + 1 >= window:
                out[i] = min(values[i - window + 1 : i + 1])
        return out

    def rolling_high(self, values, window):
        out = [None] * len(values)
        for i in range(len(values)):
            if i + 1 >= window:
                out[i] = max(values[i - window + 1 : i + 1])
        return out

    def ema(self, values, window):
        out = [None] * len(values)
        alpha = 2.0 / (window + 1.0)
        for i, v in enumerate(values):
            if v is None:
                continue
            if i == 0 or out[i - 1] is None:
                out[i] = v
            else:
                out[i] = alpha * v + (1 - alpha) * out[i - 1]
        return out

    def repulse(self, o, h, l, c, L):
        low_L = self.rolling_low(l, L)
        high_L = self.rolling_high(h, L)
        up_raw = [None] * len(c)
        down_raw = [None] * len(c)

        for i in range(len(c)):
            src_idx = i - (L - 1)
            if src_idx < 0 or low_L[i] is None or high_L[i] is None or c[i] == 0:
                continue

            open_shifted = o[src_idx]
            up_raw[i] = (((3 * c[i]) - (2 * low_L[i]) - open_shifted) * 100.0) / c[i]
            down_raw[i] = ((open_shifted - (3 * c[i]) + (2 * high_L[i])) * 100.0) / c[i]

        up = self.ema(up_raw, L * 5)
        down = self.ema(down_raw, L * 5)

        return [
            None if up[i] is None or down[i] is None else up[i] - down[i]
            for i in range(len(c))
        ]

    def compute(self, o, h, l, c, dates=None):
        indic1 = self.repulse(o, h, l, c, self.r1)
        indic5 = self.repulse(o, h, l, c, self.r2)
        indic15 = self.repulse(o, h, l, c, self.r3)
        cases = [None] * len(c)
        sentiment = ["block"] * len(c)

        for i in range(1, len(c)):
            if i < self.r3 * 5:
                continue

            if dates and dates[i] > "2030-12-05":
                cases[i] = 0
                continue

            s1 = (
                1
                if indic1[i] is not None and indic1[i - 1] is not None and indic1[i] > indic1[i - 1]
                else -1
            )
            s5 = (
                1
                if indic5[i] is not None and indic5[i - 1] is not None and indic5[i] > indic5[i - 1]
                else -1
            )
            s15 = (
                1
                if indic15[i] is not None and indic15[i - 1] is not None and indic15[i] > indic15[i - 1]
                else -1
            )

            lookup = {
                (1, 1, 1): 8,
                (1, 1, -1): 7,
                (1, -1, 1): 6,
                (1, -1, -1): 5,
                (-1, 1, 1): 4,
                (-1, 1, -1): 3,
                (-1, -1, 1): 2,
                (-1, -1, -1): 1,
            }
            cases[i] = lookup[(s15, s5, s1)]

            if self.off_on != 1:
                sentiment[i] = "pass"
            elif self.trade_only_case:
                sentiment[i] = "pass" if cases[i] == self.trade_only_case else "block"
            else:
                sentiment[i] = "block" if cases[i] in self.blocked_cases else "pass"

        return {
            "INDIC1": indic1,
            "INDIC5": indic5,
            "INDIC15": indic15,
            "CAS": cases,
            "sentiment": sentiment,
        }
```

## Notas de implementación futura
- Conviene compartir una implementación única de repulse entre este filtro y la familia de divergencias si la fórmula termina siendo exactamente común.
- La reconstrucción debe respetar que el caso solo depende del signo de la pendiente, no del valor absoluto del repulse.
- La regla dura de fecha posterior a 2030 parece una protección comercial o de expiración y debería quedar aislada como opción configurable al reconstruir.
