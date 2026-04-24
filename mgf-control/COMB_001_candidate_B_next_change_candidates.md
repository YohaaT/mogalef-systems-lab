PHASE: exploratory_control
OBJECTIVE: Enumerar los siguientes cambios mínimos candidatos sobre `COMB_001 Candidate B`.
SCOPE: Solo candidatos de cambio sobre el baseline actual. Sin ejecutar ninguno.
INPUTS: `mgf-control/COMB_001_candidate_B_iteration_plan.md`.
EXPECTED ARTIFACT: `mgf-control/COMB_001_candidate_B_next_change_candidates.md`.
STOP CONDITION: detenerse al dejar los candidatos persistidos.

# COMB_001 Candidate B next change candidates

## Candidato B1
### Nombre
Compactar horas permitidas en bloques más simples

### Cambio mínimo propuesto
Sustituir la lista discreta de horas por una o dos ventanas horarias continuas cercanas.

### Coste esperado
- bajo

### Beneficio esperado
- mayor simplicidad operativa
- mejor legibilidad del baseline
- posible mejora de robustez si la estructura temporal es real y no accidental

### Riesgo
- perder precisión si las horas buenas no se agrupan bien

## Candidato B2
### Nombre
Refinar la salida dentro del baseline temporal actual

### Cambio mínimo propuesto
Mantener las horas permitidas actuales y tocar solo una regla simple de salida distinta a `Candidate A`.

### Coste esperado
- bajo a medio

### Beneficio esperado
- mejora potencial de gestión del trade

### Riesgo
- repetir degradación si la salida se vuelve demasiado agresiva

## Candidato B3
### Nombre
Añadir confirmación mínima de señal dentro de la ventana temporal

### Cambio mínimo propuesto
Exigir una condición ligera extra sobre la señal antes de entrar, sin añadir nuevos componentes.

### Coste esperado
- medio

### Beneficio esperado
- filtrar algunas entradas débiles

### Riesgo
- arbitrariedad y exceso de restricción

## Recomendación
### Orden recomendado
1. `Candidato B1`
2. `Candidato B2`
3. `Candidato B3`

### Motivo
`Candidate B` ya mejoró por la capa temporal. El siguiente paso más lógico es simplificar y consolidar precisamente esa mejora antes de tocar otras capas.

Result:
Artifacts created:
- `mgf-control/COMB_001_candidate_B_next_change_candidates.md`
Files read:
- `mgf-control/COMB_001_candidate_B_iteration_plan.md`
Scope respected: yes
Next recommended action: si el usuario lo autoriza, ejecutar primero `Candidato B1`.
