PHASE: exploratory_control
OBJECTIVE: Comparar exclusivamente las tres ramas STPMT ya existentes para decidir la mejor candidata provisional de desarrollo.
SCOPE: Solo `COMB_001`, `COMB_004`, `COMB_007`. Sin abrir nuevas combinaciones, sin Fase 4 definitiva.
INPUTS: `mgf-control/combination_registry.md`, `mgf-control/combination_exploration_round_001.md`, `mgf-control/combination_exploration_round_002.md`, `mgf-control/combination_exploration_round_003.md`, `mgf-control/session_checkpoint.md`.
EXPECTED ARTIFACT: `mgf-control/stpmt_branch_comparison.md`.
STOP CONDITION: detenerse al dejar la comparación persistida.

# STPMT branch comparison

## Alcance de esta unidad
Comparación enfocada exclusivamente en estas tres ramas:
- `COMB_001` -> `STPMT_DIV + Trend_Filter_V2 + stop causal simple`
- `COMB_004` -> `STPMT_DIV + NeutralZone_B_V2 + stop causal simple`
- `COMB_007` -> `STPMT_DIV + Trend_Filter_V2 + NeutralZone_B_V2 + stop causal simple`

## Regla de lectura
Las métricas se usan solo como guía comparativa débil.
No se interpretan como validación fuerte ni como edge definitivo.

## Resumen comparativo
### COMB_001
- estructura: `STPMT_DIV + Trend_Filter_V2 + stop causal simple`
- frecuencia operativa observada: `97` trades
- lectura estructural:
  - es la rama más simple de las tres;
  - usa un solo filtro de régimen conocido y ya operativo;
  - coste de complejidad bajo.
- lectura provisional:
  - muy buena candidata base porque combina simplicidad, trazabilidad y suficiente actividad.

### COMB_004
- estructura: `STPMT_DIV + NeutralZone_B_V2 + stop causal simple`
- frecuencia operativa observada: `111` trades
- lectura estructural:
  - también simple, pero depende de un filtro recién reconstruido;
  - aporta una visión distinta de régimen/contexto frente a Trend Filter V2;
  - coste de complejidad todavía bajo.
- lectura provisional:
  - candidata interesante y competitiva;
  - útil como rama alternativa principal dentro de STPMT.

### COMB_007
- estructura: `STPMT_DIV + Trend_Filter_V2 + NeutralZone_B_V2 + stop causal simple`
- frecuencia operativa observada: `64` trades
- lectura estructural:
  - doble filtro;
  - mayor complejidad lógica;
  - menor frecuencia operativa;
  - más coste de mantenimiento e interpretación por filtro adicional.
- lectura provisional:
  - útil como rama de confirmación/restricción;
  - menos atractiva como rama principal por complejidad extra y reducción de actividad.

## Comparación por criterio
### 1. Frecuencia operativa
- `COMB_004`: más alta (`111`)
- `COMB_001`: intermedia (`97`)
- `COMB_007`: más baja (`64`)

### 2. Estabilidad relativa
Lectura provisional no basada en edge fuerte, sino en equilibrio entre actividad y simplicidad:
- `COMB_001` parece la más estable para seguir iterando porque no introduce doble filtro ni dependencia de una pieza recién añadida.
- `COMB_004` queda cerca y es una alternativa muy válida.
- `COMB_007` parece más frágil por exceso relativo de filtrado en esta etapa.

### 3. Simplicidad estructural
- más simple: `COMB_001`
- simple pero algo menos consolidada: `COMB_004`
- más compleja: `COMB_007`

### 4. Coste de complejidad por filtro adicional
- `COMB_001`: bajo
- `COMB_004`: bajo
- `COMB_007`: claramente mayor por doble filtro y menor claridad interpretativa en esta etapa

## Ranking provisional final de la rama STPMT
### 1) Mejor candidata provisional actual
**`COMB_001`**

Motivo:
- mejor equilibrio entre simplicidad, actividad suficiente y coste bajo de interpretación.
- es la mejor rama para seguir desarrollando primero sin sobrecargar la lógica.

### 2) Segunda candidata provisional
**`COMB_004`**

Motivo:
- rama competitiva, simple y con frecuencia algo mayor.
- merece seguir viva como alternativa principal dentro de STPMT.

### 3) Tercera candidata provisional
**`COMB_007`**

Motivo:
- útil como rama de confirmación más estricta, pero no como principal en esta etapa.
- el filtro adicional añade complejidad sin justificar todavía prioridad superior.

## Dictamen de esta unidad
- candidata provisional principal para seguir desarrollando: `COMB_001`
- candidata provisional secundaria a mantener activa: `COMB_004`
- candidata de menor prioridad dentro de esta tríada: `COMB_007`

Result:
Artifacts created:
- `mgf-control/stpmt_branch_comparison.md`
Files read:
- `mgf-control/combination_registry.md`
- `mgf-control/combination_exploration_round_001.md`
- `mgf-control/combination_exploration_round_002.md`
- `mgf-control/combination_exploration_round_003.md`
- `mgf-control/session_checkpoint.md`
Scope respected: yes
Next recommended action: desarrollar primero `COMB_001` y mantener `COMB_004` como rama secundaria viva dentro de STPMT.
