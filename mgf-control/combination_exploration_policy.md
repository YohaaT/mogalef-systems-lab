PHASE: control
OBJECTIVE: Persistir el nuevo objetivo operativo del proyecto para exploración disciplinada de combinaciones, sin tratar métricas actuales como validación fuerte.
SCOPE: Política de exploración y etiquetado de combinaciones.
INPUTS: nueva directriz explícita del usuario.
EXPECTED ARTIFACT: `mgf-control/combination_exploration_policy.md`.
STOP CONDITION: detenerse al dejar la nueva política persistida.

# Combination exploration policy

## Nuevo objetivo operativo
Seguir creando y evaluando combinaciones de componentes para explorar comportamiento relativo, no para validar edge definitivo.

## Reglas vigentes
1. métricas actuales (`R:R`, win rate, profit factor, net points, etc.) sirven solo como guía orientativa débil;
2. no presentar ningún resultado actual como validación seria del sistema;
3. seguir construyendo combinaciones aunque el backtest aún no sea completamente confiable;
4. cada combinación debe llevar una etiqueta de calidad de esta lista:
   - `provisional_usable_for_ranking`
   - `contaminated_by_noncausal_component`
   - `blocked_for_strategy_use`
5. si una combinación usa `EL_MOGALEF_Bands` o `EL_Stop_Intelligent` en modo no causal, marcarla como `contaminated_by_noncausal_component`;
6. no detener el flujo solo porque las métricas parezcan demasiado buenas;
7. sí detener el flujo solo ante:
   - bloqueo técnico real
   - falta de datos
   - inconsistencia de integración
   - gate de fase real

## Línea de trabajo prioritaria
- seguir creando combinaciones mínimas y compararlas de forma exploratoria;
- documentar qué combinación parece prometedora;
- documentar qué combinación queda contaminada;
- no obsesionarse con limpieza total de métricas en esta etapa.

## Orden de trabajo
1. diseñar wrappers causales solo cuando bloqueen demasiado la exploración;
2. mientras tanto, seguir probando combinaciones y etiquetarlas correctamente;
3. priorizar entradas y filtros nuevos antes que más stops o más estructura.

## Próximas prioridades de combinación
Explorar combinaciones de:
- `EL_STPMT_DIV`
- `EL_REPULSE_DIV`

con:
- `EL_Mogalef_Trend_Filter_V2`
- `EL_NeutralZone_B_V2`
- `EL_MOGALEF_Bands` (marcado como provisional/contaminado si sigue no causal)
- `EL_Stop_Intelligent` (marcado como provisional/contaminado si sigue no causal)

## Salida mínima exigida en adelante
Para cada combinación probada, dejar:
- registro de combinación;
- etiqueta de calidad;
- nota breve de interpretación;
- métricas usadas solo como guía comparativa, nunca como prueba final.

Result:
Artifacts created:
- `mgf-control/combination_exploration_policy.md`
Files read:
- directriz explícita del usuario en esta conversación
Scope respected: yes
Next recommended action: abrir registro disciplinado de combinaciones probadas y empezar por `STPMT_DIV` / `REPULSE_DIV` con filtros priorizados.
