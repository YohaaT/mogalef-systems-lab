PHASE: exploratory_control
OBJECTIVE: Aplicar la mejora mínima `Candidato A` sobre `COMB_001`, refinando solo la capa de salida/riesgo.
SCOPE: Solo ajuste de salida de `COMB_001`. Sin tocar entrada, sin tocar filtro, sin abrir nuevas combinaciones.
INPUTS: `mgf-control/strategy_candidate_COMB_001.md`, `mgf-control/strategy_candidate_COMB_001_rules.md`, `mgf-control/COMB_001_iteration_plan.md`, `mgf-control/COMB_001_next_change_candidates.md`.
EXPECTED ARTIFACT: `mgf-control/COMB_001_candidate_A_impl.md`.
STOP CONDITION: detenerse al dejar la implementación lógica persistida.

# COMB_001 candidate A implementation

## 1. Cambio exacto aplicado
Se refina la salida causal simple de `COMB_001` añadiendo una única mejora mínima:

**regla de break-even simple tras avance favorable suficiente**.

## 2. Qué se mantiene intacto
No cambia nada en:
- entrada `STPMT_DIV`
- filtro `EL_Mogalef_Trend_Filter_V2`
- convención temporal de señal y ejecución
- una sola posición a la vez

## 3. Nueva lógica de salida
### Base anterior
- stop inicial = extremo de la barra de señal
- salida por stop o por señal opuesta válida

### Mejora actual
Además de la lógica base:
- si la posición avanza al menos `+1R` a favor desde la entrada,
- el stop deja de quedarse en el nivel inicial,
- y se mueve a **break-even** (precio de entrada).

## 4. Por qué este cambio es el correcto primero
- sigue siendo causal y simple
- toca solo una capa
- no altera la identidad de la rama principal
- reduce el coste de dejar trades ganadores volver a pérdida completa
- mantiene comparabilidad alta con la versión base

## 5. Qué cambia respecto a COMB_001 base
### Antes
- el riesgo inicial permanecía fijo hasta stop o salida por señal opuesta.

### Ahora
- el riesgo inicial sigue naciendo igual,
- pero si el trade demuestra avance suficiente (`1R`),
- la estrategia protege capital subiendo el stop a break-even.

## 6. Qué no se añade todavía
- no hay trailing complejo
- no hay target fijo
- no hay salidas parciales
- no hay money management nuevo
- no hay nueva lógica de entrada
- no hay nueva lógica de filtro

## 7. Qué quedará pendiente para evaluar después
1. si el paso a break-even mejora claridad operativa sin sobrecomplicar;
2. si reduce pérdidas evitables tras avances favorables;
3. si merece una siguiente iteración simple sobre gestión temporal o salida por tiempo.

## 8. Identidad resultante de la rama
`COMB_001` sigue siendo la misma rama principal.
La única diferencia es que su salida deja de ser un stop fijo totalmente pasivo y pasa a ser una salida causal simple con protección a break-even tras `1R` favorable.

Result:
Artifacts created:
- `mgf-control/COMB_001_candidate_A_impl.md`
Files read:
- `mgf-control/strategy_candidate_COMB_001.md`
- `mgf-control/strategy_candidate_COMB_001_rules.md`
- `mgf-control/COMB_001_iteration_plan.md`
- `mgf-control/COMB_001_next_change_candidates.md`
Scope respected: yes
Next recommended action: usar esta versión como siguiente variante controlada de la rama principal cuando se autorice evaluación.
