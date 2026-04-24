PHASE: exploratory_control
OBJECTIVE: Enumerar los siguientes cambios mínimos candidatos sobre `COMB_001` y su coste/beneficio esperado.
SCOPE: Solo candidatos de cambio sobre la rama principal. Sin ejecutar ninguno.
INPUTS: `mgf-control/COMB_001_iteration_plan.md`.
EXPECTED ARTIFACT: `mgf-control/COMB_001_next_change_candidates.md`.
STOP CONDITION: detenerse al dejar los candidatos persistidos.

# COMB_001 next change candidates

## Candidato A
### Nombre
Refinar la salida causal simple

### Cambio mínimo propuesto
Mantener entrada y filtro intactos, cambiando solo la lógica de salida mínima.

### Coste esperado
- bajo
- una sola capa tocada
- comparación simple contra baseline

### Beneficio esperado
- mejora de claridad operativa
- mejor lectura de comportamiento del trade
- posible mejora del equilibrio entre pérdidas pequeñas y capturas válidas

### Riesgo
- puede no mejorar nada
- podría reducir comparabilidad si se añade demasiada lógica

## Candidato B
### Nombre
Restringir temporalmente las entradas de COMB_001

### Cambio mínimo propuesto
Mantener toda la lógica base y limitar entradas a un subconjunto horario simple.

### Coste esperado
- bajo a medio
- necesita apoyarse en el análisis horario ya acumulado

### Beneficio esperado
- posible reducción de ruido operativo
- mejora interpretativa por franja

### Riesgo
- sesgo de muestra en dataset corto
- riesgo de sobreajuste prematuro si se hace demasiado fino

## Candidato C
### Nombre
Endurecer mínimamente la señal STPMT dentro de la misma rama

### Cambio mínimo propuesto
Exigir una condición adicional ligera sobre la señal, sin añadir componentes nuevos.

### Coste esperado
- medio
- requiere decidir una regla interna no arbitraria

### Beneficio esperado
- puede filtrar entradas débiles manteniendo la rama intacta

### Riesgo
- más fácil introducir arbitrariedad
- más difícil justificar que tocar la salida primero

## Recomendación
### Orden recomendado
1. `Candidato A`
2. `Candidato B`
3. `Candidato C`

### Motivo
El mayor límite actual de `COMB_001` está en la crudeza de la salida. Por eso el primer cambio lógico debe ser mejorar esa parte sin mover todavía entrada ni filtro.

Result:
Artifacts created:
- `mgf-control/COMB_001_next_change_candidates.md`
Files read:
- `mgf-control/COMB_001_iteration_plan.md`
Scope respected: yes
Next recommended action: si el usuario lo autoriza, ejecutar primero el `Candidato A`.
