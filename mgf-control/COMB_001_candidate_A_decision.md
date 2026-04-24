PHASE: exploratory_control
OBJECTIVE: Registrar y persistir el resultado de `Candidate A` como intento fallido sobre `COMB_001`.
SCOPE: Solo decisión final sobre `Candidate A`.
INPUTS: `mgf-control/COMB_001_candidate_A_comparison.md`, `mgf-control/COMB_001_candidate_A_summary.md`.
EXPECTED ARTIFACT: `mgf-control/COMB_001_candidate_A_decision.md`.
STOP CONDITION: detenerse al dejar la decisión persistida.

# COMB_001 Candidate A decision

## Resultado fijado
- `COMB_001` base se mantiene
- `Candidate A` queda descartado
- dictamen formal: `keep_base`

## Qué fue Candidate A
Añadir break-even tras `1R` favorable, sin cambiar entrada ni filtro.

## Motivo del descarte
En esta muestra práctica:
- generó demasiados cierres planos (`break-even`)
- degradó el neto orientativo
- no mejoró la rama principal

## Decisión operativa
`Candidate A` no pasa a ser la nueva base y queda registrado como intento fallido dentro de la línea de desarrollo de `COMB_001`.

Result:
Artifacts created:
- `mgf-control/COMB_001_candidate_A_decision.md`
Files read:
- `mgf-control/COMB_001_candidate_A_comparison.md`
- `mgf-control/COMB_001_candidate_A_summary.md`
Scope respected: yes
Next recommended action: probar `Candidate B` manteniendo intacta la base salvo el cambio permitido por el plan.
