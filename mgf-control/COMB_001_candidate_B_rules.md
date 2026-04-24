PHASE: exploratory_control
OBJECTIVE: Dejar las reglas operativas de `COMB_001 Candidate B`.
SCOPE: Solo reglas de Candidate B. Sin nuevas combinaciones.
INPUTS: `mgf-control/COMB_001_candidate_B_impl.md`, `mgf-control/strategy_candidate_COMB_001_rules.md`.
EXPECTED ARTIFACT: `mgf-control/COMB_001_candidate_B_rules.md`.
STOP CONDITION: detenerse al dejar reglas persistidas.

# COMB_001 Candidate B rules

## Base intacta
- entrada: `EL_STPMT_DIV`
- filtro: `EL_Mogalef_Trend_Filter_V2`
- salida: stop causal simple base

## Cambio único de Candidate B
Solo permitir nuevas entradas si la hora UTC de la barra de señal pertenece a:
- `13`
- `14`
- `18`
- `21`
- `22`

## Regla larga
Abrir largo en `t+1` solo si:
1. `STPMT_DIV pose = 1`
2. `Trend_Filter_V2 sentiment = pass`
3. hora UTC de la barra de señal en el conjunto permitido
4. no existe posición abierta

## Regla corta
Abrir corto en `t+1` solo si:
1. `STPMT_DIV pose = -1`
2. `Trend_Filter_V2 sentiment = pass`
3. hora UTC de la barra de señal en el conjunto permitido
4. no existe posición abierta

## Salida
Sin cambios respecto a la base:
- salida por stop causal simple
- o por señal opuesta válida
- o por final de dataset/run

Result:
Artifacts created:
- `mgf-control/COMB_001_candidate_B_rules.md`
Files read:
- `mgf-control/COMB_001_candidate_B_impl.md`
- `mgf-control/strategy_candidate_COMB_001_rules.md`
Scope respected: yes
Next recommended action: usar estas reglas para la comparación ligera base vs Candidate B.
