PHASE: exploratory_control
OBJECTIVE: Dejar especificada de forma operativa y reusable la rama principal `COMB_001`.
SCOPE: Solo definición estratégica de `COMB_001`. Sin nuevas combinaciones, sin Fase 4.
INPUTS: `mgf-control/stpmt_branch_comparison.md`, `mgf-control/combination_registry.md`, artefactos previos de backtest causal ligero de la rama STPMT.
EXPECTED ARTIFACT: `mgf-control/strategy_candidate_COMB_001.md`.
STOP CONDITION: detenerse al dejar la estrategia candidata persistida.

# Strategy candidate COMB_001

## 1. Estado de la rama
`COMB_001` pasa a ser la **rama principal de desarrollo** dentro del proyecto.

## 2. Componentes exactos usados
- `EL_STPMT_DIV`
- `EL_Mogalef_Trend_Filter_V2`
- stop causal simple

## 3. Rol de cada componente
### `EL_STPMT_DIV`
Motor principal de entrada.
Su función es detectar el disparo operativo long/short.

### `EL_Mogalef_Trend_Filter_V2`
Filtro de régimen/contexto.
Su función es permitir o bloquear la operación según el sesgo del mercado.

### Stop causal simple
Gestión de salida/riesgo mínima.
Su función es definir una pérdida máxima simple y secuencial, sin usar todavía stops retrospectivos contaminados.

## 4. Qué hace realmente esta estrategia
La estrategia intenta operar señales STPMT solo cuando el filtro de régimen lo permite.
Una vez dentro, protege la posición con un stop causal simple y puede salir también por señal opuesta válida.

Traducido a una frase:
> entrar cuando `STPMT_DIV` dispara en una dirección y `Trend_Filter_V2` no bloquea esa lectura, usando una salida simple y causal para mantener la rama limpia y reusable.

## 5. Filtro / contexto actual
Contexto actual permitido:
- filtro de régimen: `EL_Mogalef_Trend_Filter_V2`
- sin estructura adicional obligatoria
- sin bandas
- sin stop inteligente

Esto se hace a propósito para mantener la rama principal simple y lo menos contaminada posible.

## 6. Salida / riesgo actual
Salida mínima actual:
- stop causal simple basado en la barra de señal
- salida por señal opuesta válida si aparece antes del stop
- una sola posición a la vez
- sin pyramiding
- sin money management avanzado
- sin target fijo obligatorio en esta etapa

## 7. Orden temporal de evaluación
La convención operativa actual de esta rama es:
1. observar señal en barra cerrada `t`
2. comprobar filtro en esa misma barra `t`
3. si la condición es válida, ejecutar en apertura de `t+1`
4. activar el stop después de la entrada real
5. gestionar barra a barra de forma causal

## 8. Supuestos actuales
- `STPMT_DIV` es el motor de entrada prioritario de trabajo
- `Trend_Filter_V2` es el filtro principal vigente
- el stop causal simple es una solución temporal limpia para exploración disciplinada
- las métricas actuales se usan solo para ranking provisional, no para validación fuerte

## 9. Límites y advertencias
- esta rama no debe presentarse como estrategia validada definitivamente
- el dataset usado hasta ahora es práctico y limitado
- no hay todavía validación histórica seria
- no se está afirmando edge definitivo
- futuras iteraciones pueden cambiar frecuencia, salida o robustez sin invalidar la utilidad actual de esta rama como base principal

## 10. Siguientes iteraciones lógicas permitidas sobre esta rama
Sin abrir todavía Fase 4 definitiva, las siguientes iteraciones naturales sobre `COMB_001` serían:
1. análisis horario específico de la rama
2. ajuste disciplinado de reglas de salida causal simple
3. comparación interna de variantes de salida simples sin introducir componentes retrospectivos contaminados
4. reintroducción futura de estructura o stops más complejos solo si se hacen de forma causal y sin bloquear la exploración

## 11. Posición relativa dentro del proyecto
- rama principal actual: `COMB_001`
- rama secundaria activa: `COMB_004`
- rama depriorizada: `COMB_007`

Result:
Artifacts created:
- `mgf-control/strategy_candidate_COMB_001.md`
Files read:
- `mgf-control/stpmt_branch_comparison.md`
- `mgf-control/combination_registry.md`
- artefactos previos de la rama STPMT
Scope respected: yes
Next recommended action: usar `COMB_001` como base principal para próximas iteraciones lógicas controladas.
