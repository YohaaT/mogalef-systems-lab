PHASE: exploratory_control
OBJECTIVE: Comparar `COMB_001` base frente a `COMB_001 Candidate B` con el mismo dataset y mismo alcance ligero.
SCOPE: Solo comparación base vs Candidate B. Sin nuevas ramas. Sin Fase 4 definitiva.
INPUTS: `mgf-control/strategy_candidate_COMB_001_rules.md`, `mgf-control/COMB_001_candidate_B_rules.md`, mismo dataset práctico `MNQ 5m`.
EXPECTED ARTIFACT: `mgf-control/COMB_001_candidate_B_comparison.md`.
STOP CONDITION: detenerse al dejar comparación persistida.

# COMB_001 Candidate B comparison

## 1. Qué cambia y qué no cambia
### Se mantiene igual
- entrada: `EL_STPMT_DIV`
- filtro: `EL_Mogalef_Trend_Filter_V2`
- salida: stop causal simple base
- dataset
- instrumento
- timeframe
- convención temporal

### Lo único que cambia
- restricción horaria de entrada

## 2. Resultado orientativo de la base
- trades: `97`
- wins: `17`
- losses: `80`
- flats: `0`
- net points: `1369.5`
- avg points: `14.1186`

## 3. Resultado orientativo de Candidate B
- trades: `19`
- wins: `10`
- losses: `9`
- flats: `0`
- net points: `1769.25`
- avg points: `93.1184`
- horas permitidas: `13`, `14`, `18`, `21`, `22` UTC

## 4. Lectura comparativa breve
`Candidate B` reduce fuertemente la frecuencia operativa, pero mejora la lectura orientativa de la rama en esta muestra concreta.

No significa validación fuerte.
Sí significa que, como variante ligera y disciplinada sobre la misma rama, esta restricción temporal parece más prometedora que la base en esta ventana de datos.

## 5. Dictamen final
- Dictamen: `keep_candidate_B`

## 6. Motivo del dictamen
A diferencia de `Candidate A`, esta iteración mínima sí mejora la comparación orientativa sin cambiar la identidad central de la rama.

Result:
Artifacts created:
- `mgf-control/COMB_001_candidate_B_comparison.md`
Files read:
- `mgf-control/strategy_candidate_COMB_001_rules.md`
- `mgf-control/COMB_001_candidate_B_rules.md`
- mismo dataset práctico `MNQ 5m`
Scope respected: yes
Next recommended action: si se desea seguir esta línea, promover provisionalmente `Candidate B` como nueva variante principal de trabajo dentro de `COMB_001`.
