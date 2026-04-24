# EL_NeutralZone_B_V2 - Ambigüedades abiertas

## 1. Valor real de `VueTrend`
El input se declara como `"Yes;No",0`, pero el código entra en la rama visible cuando `VueTrend=0`. Eso implica que el índice `0` corresponde a `Yes`. Hay que preservar esa convención exacta al reconstruir.

## 2. Comportamiento cuando `VueTrend=No`
Si `milieu=void`, luego `band[i]=milieu[i]`, pero más abajo el código puede intentar sumar o restar ticks a `milieu`. La plataforma quizá tolera esto; en Python habrá que decidir si `band` también queda `None` o si se calcula aparte sin pintar.

## 3. Persistencia de `marqueurRET`
Cuando `RET` no cambia, hereda `marqueurRET[i+1]`. En barras iniciales esa referencia puede no existir todavía. La reconstrucción debe inicializar bien el primer valor para no crear direcciones fantasmas.

## 4. Modo `signal`
La intención es emitir pulsos solo en cambio de consenso, pero el código usa condiciones sobre `i+1` dentro de un recorrido retrospectivo. Antes de Fase 2 habrá que fijar exactamente qué barra cronológica recibe el pulso.

## 5. Significado operativo de `100/50/0`
El componente usa convención clásica de sentimiento Mogalef, pero en `UseAs=filter` y `UseAs=signal` el significado cambia ligeramente: persistencia frente a pulso. Conviene documentarlo explícitamente en la capa Python.
