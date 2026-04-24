# EL_Stop_Intelligent - Ambigüedades abiertas

## 1. Orientación temporal de índices
El lenguaje fuente usa acceso tipo `i+1`, `i+2` dentro de bucles retrospectivos y además mezcla series directas con referencias `[1]`. Antes de reconstruir, hay que fijar una convención cronológica exacta para no invertir los pivots.

## 2. Persistencia de `flaglong`
El código actualiza `flaglong` solo cuando `MarketPosition()` vale `1` o `-1`. No define explícitamente qué ocurre al volver a `0`. Hay que decidir si la versión Python mantiene el último valor o si resetea al quedar flat.

## 3. `space` potencialmente negativo
La fórmula permite `space < 0` cuando la volatilidad reciente supera mucho la de referencia. El código usa `absvalue(space)` en clamps, pero no en la fórmula principal. Conviene preservar ese comportamiento y documentarlo como deliberado, no corregirlo en Fase 1.

## 4. `WaitForXtrem` en la versión base
La lógica existe, pero la variante live la reorganiza y corrige. Antes de Fase 2 habrá que decidir si la implementación canónica toma la base literal o incorpora la corrección live como fix operativo.

## 5. Serie única `stoplong` para ambos lados
El fuente base reutiliza `stoplong` también en cortos. Funciona en plataforma original, pero en Python probablemente convenga separar `stop_long_active` y `stop_short_active` para evitar ambigüedad semántica sin cambiar resultado.

## 6. Barras iniciales sin pivots suficientes
El código no define una política explícita cuando todavía no existen `B2`, `B3`, `H2`, `H3` o ATR completos. La reconstrucción deberá dejar `None/NaN` hasta tener historia suficiente.
