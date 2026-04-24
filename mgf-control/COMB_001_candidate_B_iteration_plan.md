PHASE: exploratory_control
OBJECTIVE: Preparar la siguiente iteración controlada de `COMB_001` usando `Candidate B` como rama derivada activa, manteniendo `COMB_001` base como matriz principal.
SCOPE: Solo planificación sobre la rama derivada activa `COMB_001 Candidate B`. Sin nuevas combinaciones. Sin Fase 4.
INPUTS: `mgf-control/COMB_001_candidate_B_impl.md`, `mgf-control/COMB_001_candidate_B_comparison.md`, `mgf-control/COMB_001_candidate_B_summary.md`, `mgf-control/strategy_candidate_COMB_001_rules.md`.
EXPECTED ARTIFACT: `mgf-control/COMB_001_candidate_B_iteration_plan.md`.
STOP CONDITION: detenerse al dejar el plan persistido.

# COMB_001 Candidate B iteration plan

## 1. Estado actual de Candidate B
`COMB_001 Candidate B` queda como rama derivada activa.
`COMB_001` base sigue siendo la matriz/base principal del proyecto.

Composición actual:
- `EL_STPMT_DIV`
- `EL_Mogalef_Trend_Filter_V2`
- stop causal simple base
- restricción horaria mínima de entrada: `13`, `14`, `18`, `21`, `22` UTC

## 2. Qué mejoró respecto a la base
En la comparación ligera sobre el mismo dataset práctico:
- redujo la frecuencia operativa
- mejoró el neto orientativo
- mejoró el promedio por trade

Lectura correcta:
- no es validación definitiva
- sí es una mejora comparativa suficiente para mantenerlo como rama derivada activa de trabajo

## 3. Límites actuales
1. la restricción horaria actual todavía es discreta y algo rígida;
2. la salida sigue siendo simple y no está refinada dentro de esta rama derivada activa;
3. el conjunto horario puede estar capturando señal útil real o puede estar absorbiendo ruido de muestra;
4. todavía falta una siguiente mejora mínima que conserve trazabilidad y comparabilidad.

## 4. Cambios mínimos candidatos
### Candidato B1
**Compactar la restricción horaria en bloques más simples**

Idea:
- pasar de horas discretas a 1 o 2 ventanas horarias continuas cercanas;
- mantener la misma filosofía temporal;
- reducir complejidad operativa.

### Candidato B2
**Refinar mínimamente la salida sin tocar entrada ni filtro ni ventana horaria**

Idea:
- mantener `Candidate B` intacto como rama derivada temporal;
- tocar solo la capa de salida con una mejora simple distinta de `Candidate A`.

### Candidato B3
**Exigir confirmación temporal mínima de persistencia de señal dentro de Candidate B**

Idea:
- mantener misma ventana horaria;
- no cambiar componentes;
- pedir una confirmación ligera adicional sobre la señal antes de entrar.

## 5. Coste/beneficio esperado
### Candidato B1
- coste: bajo
- beneficio esperado: simplificación operativa y mejor legibilidad
- riesgo: perder parte de la mejora si las horas buenas no forman bloques limpios

### Candidato B2
- coste: bajo a medio
- beneficio esperado: mejorar gestión de trade dentro de la rama derivada ya fortalecida
- riesgo: repetir un problema parecido al de `Candidate A` si la salida se vuelve demasiado agresiva

### Candidato B3
- coste: medio
- beneficio esperado: filtrar algunas entradas débiles manteniendo la rama intacta
- riesgo: introducir más arbitrariedad y reducir demasiado la frecuencia

## 6. Recomendación principal
### Probar primero: Candidato B1
**compactar la restricción horaria en bloques más simples**

## 7. Por qué recomiendo B1 primero
- parte del cambio que ya mejoró respecto a la base;
- intenta simplificar, no complicar;
- mantiene intacta la identidad de la rama derivada activa;
- permite comprobar si la mejora horaria tiene estructura más robusta que un conjunto de horas sueltas.

## 8. Por qué conviene seguir iterando esta rama en vez de abrir otras
- esta rama ya mostró una mejora comparativa orientativa;
- abrir otras ramas ahora rompería continuidad de aprendizaje;
- seguir iterando `COMB_001 Candidate B` conserva disciplina y acumulación de evidencia dentro de la misma línea derivada, sin perder la referencia madre `COMB_001` base.

Result:
Artifacts created:
- `mgf-control/COMB_001_candidate_B_iteration_plan.md`
Files read:
- `mgf-control/COMB_001_candidate_B_impl.md`
- `mgf-control/COMB_001_candidate_B_comparison.md`
- `mgf-control/COMB_001_candidate_B_summary.md`
- `mgf-control/strategy_candidate_COMB_001_rules.md`
Scope respected: yes
Next recommended action: si se autoriza, probar primero `Candidato B1` sobre la rama derivada activa `COMB_001 Candidate B`, manteniendo visible la referencia contra `COMB_001` base.
