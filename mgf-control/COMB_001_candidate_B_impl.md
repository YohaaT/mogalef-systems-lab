PHASE: exploratory_control
OBJECTIVE: Preparar y ejecutar `Candidate B` sobre `COMB_001` manteniendo intacta la identidad de la rama principal.
SCOPE: Solo cambio mínimo permitido sobre `COMB_001`. Sin nuevas combinaciones. Sin Fase 4.
INPUTS: `mgf-control/COMB_001_iteration_plan.md`, `mgf-control/COMB_001_next_change_candidates.md`, `mgf-control/strategy_candidate_COMB_001_rules.md`, trade log horario acumulado de la rama.
EXPECTED ARTIFACT: `mgf-control/COMB_001_candidate_B_impl.md`.
STOP CONDITION: detenerse al dejar Candidate B persistido y comparado.

# COMB_001 Candidate B implementation

## 1. Qué fue exactamente Candidate B
`Candidate B` consiste en una **restricción temporal mínima de entrada** sobre `COMB_001`.

## 2. Cambio exacto aplicado
Se mantiene intacta la lógica base de `COMB_001`, pero las entradas solo se permiten cuando la barra de señal cae dentro de estas horas UTC:
- `13`
- `14`
- `18`
- `21`
- `22`

## 3. Qué no cambia
- entrada: `EL_STPMT_DIV`
- filtro: `EL_Mogalef_Trend_Filter_V2`
- salida/riesgo: stop causal simple base
- dataset
- instrumento
- timeframe
- convención temporal

## 4. Por qué este cambio era el siguiente lógico
- es mínimo y reversible;
- no abre una nueva combinación;
- usa información ya observada en la propia rama principal;
- mejora potencialmente la limpieza operativa sin tocar ni entrada ni filtro.

## 5. Cómo cambia la lógica respecto a COMB_001 base
### Base
Si hay señal STPMT válida y el filtro permite operar, se entra.

### Candidate B
Si hay señal STPMT válida y el filtro permite operar, **solo se entra además si la hora UTC está dentro del subconjunto permitido**.

## 6. Qué queda pendiente para evaluar después
- si esta restricción horaria se sostiene mejor en más muestra o era solo un efecto de la ventana actual;
- si merece una versión aún más simple por bloque horario en vez de horas discretas;
- si conviene mantener `Candidate B` o volver a la base como rama principal vigente.

Result:
Artifacts created:
- `mgf-control/COMB_001_candidate_B_impl.md`
Files read:
- `mgf-control/COMB_001_iteration_plan.md`
- `mgf-control/COMB_001_next_change_candidates.md`
- `mgf-control/strategy_candidate_COMB_001_rules.md`
- trade log horario acumulado de la rama principal
Scope respected: yes
Next recommended action: comparar `Candidate B` contra la base con el mismo dataset y mismo alcance ligero.
