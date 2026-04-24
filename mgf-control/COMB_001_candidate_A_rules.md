PHASE: exploratory_control
OBJECTIVE: Dejar las reglas operativas de `COMB_001` tras aplicar `Candidato A`.
SCOPE: Solo reglas de salida/riesgo refinadas. Sin cambiar entrada ni filtro.
INPUTS: `mgf-control/COMB_001_candidate_A_impl.md`, `mgf-control/strategy_candidate_COMB_001_rules.md`.
EXPECTED ARTIFACT: `mgf-control/COMB_001_candidate_A_rules.md`.
STOP CONDITION: detenerse al dejar reglas persistidas.

# COMB_001 candidate A rules

## Base intacta
- entrada: `EL_STPMT_DIV`
- filtro: `EL_Mogalef_Trend_Filter_V2`
- ejecución: señal en `t`, entrada en apertura de `t+1`

## Salida/riesgo refinada
### 1. Stop inicial
#### Si la entrada es larga
- stop inicial = mínimo de la barra de señal

#### Si la entrada es corta
- stop inicial = máximo de la barra de señal

### 2. Activación de break-even
#### En largos
Si el precio alcanza al menos `entry_price + 1R`, donde `R = entry_price - initial_stop`, entonces:
- el stop se mueve a `entry_price`

#### En cortos
Si el precio alcanza al menos `entry_price - 1R`, donde `R = initial_stop - entry_price`, entonces:
- el stop se mueve a `entry_price`

## 3. Salida
Cerrar la posición si ocurre cualquiera de estas condiciones:
1. el precio toca el stop activo actual
2. aparece una señal opuesta válida y el filtro sigue permitiendo operar
3. se llega al final del dataset/run usado

## 4. Qué cambia frente a la base
- antes: el stop quedaba fijo en el nivel inicial
- ahora: tras `1R` favorable, el stop se protege en break-even

## 5. Qué sigue igual
- misma entrada
- mismo filtro
- misma secuencia temporal
- una sola posición a la vez
- sin target fijo
- sin trailing adicional

## 6. Propósito operativo
Este cambio busca mejorar la disciplina de protección sin introducir complejidad innecesaria ni desviar la rama principal de su identidad actual.

Result:
Artifacts created:
- `mgf-control/COMB_001_candidate_A_rules.md`
Files read:
- `mgf-control/COMB_001_candidate_A_impl.md`
- `mgf-control/strategy_candidate_COMB_001_rules.md`
Scope respected: yes
Next recommended action: si el usuario lo autoriza, evaluar esta variante contra la base de `COMB_001` en una unidad comparativa posterior.
