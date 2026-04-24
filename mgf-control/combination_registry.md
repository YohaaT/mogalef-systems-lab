# Combination registry

## Estado del registro
Activo.

## Etiquetas válidas
- `provisional_usable_for_ranking`
- `contaminated_by_noncausal_component`
- `blocked_for_strategy_use`

## Combinaciones registradas

### COMB_001
- componentes: `EL_STPMT_DIV` + `EL_Mogalef_Trend_Filter_V2` + stop causal simple
- dataset: `MNQ 5m` práctico
- estado: `provisional_usable_for_ranking`
- rol actual: matriz/base principal del proyecto
- interpretación breve: primera combinación causal ligera usable para ranking exploratorio y referencia madre para comparar variantes derivadas; métricas solo orientativas.

#### Variantes derivadas vigentes de COMB_001
- `Candidate A`: variante derivada de salida, descartada con dictamen `keep_base`.
- `Candidate B`: variante derivada activa, basada en restricción horaria mínima de entrada; toda comparación importante debe seguir manteniendo visible la referencia contra `COMB_001` base.

### COMB_002
- componentes: `EL_STPMT_DIV` + `EL_Mogalef_Trend_Filter_V2` + `EL_MOGALEF_Bands` + `EL_Stop_Intelligent`
- dataset: `MNQ 5m` práctico
- estado: `contaminated_by_noncausal_component`
- interpretación breve: combinación estructuralmente interesante pero contaminada por uso no causal de `Bands` y `Stop Intelligent`.

### COMB_003
- componentes: `EL_STPMT_DIV` + `EL_Mogalef_Trend_Filter_V2` + `EL_MOGALEF_Bands` (reintroducción conservadora) + stop causal simple
- dataset: `MNQ 5m` práctico
- estado: `contaminated_by_noncausal_component`
- interpretación breve: la reintroducción de `Bands` no cambió el comportamiento en la muestra y sigue sin aportar valor causal claro.

### COMB_004
- componentes: `EL_STPMT_DIV` + `EL_NeutralZone_B_V2` + stop causal simple
- dataset: `MNQ 5m` práctico
- estado: `provisional_usable_for_ranking`
- interpretación breve: combinación desbloqueada tras rebuild de `EL_NeutralZone_B_V2`; usable para ranking provisional y comparable con la rama `Trend_Filter_V2`.

### COMB_005
- componentes: `EL_REPULSE_DIV` + `EL_Mogalef_Trend_Filter_V2` + stop causal simple
- dataset: `MNQ 5m` práctico
- estado: `provisional_usable_for_ranking`
- interpretación breve: combinación causal ligera usable para ranking exploratorio; comportamiento mucho más flojo que `STPMT_DIV + Trend Filter V2` en esta muestra, pero válida para comparación.

### COMB_006
- componentes: `EL_REPULSE_DIV` + `EL_NeutralZone_B_V2` + stop causal simple
- dataset: `MNQ 5m` práctico
- estado: `provisional_usable_for_ranking`
- interpretación breve: combinación desbloqueada tras rebuild de `EL_NeutralZone_B_V2`; en esta muestra queda por detrás y con neto negativo, pero sigue siendo usable para ranking provisional.

### COMB_007
- componentes: `EL_STPMT_DIV` + `EL_Mogalef_Trend_Filter_V2` + `EL_NeutralZone_B_V2` + stop causal simple
- dataset: `MNQ 5m` práctico
- estado: `provisional_usable_for_ranking`
- interpretación breve: combinación más restrictiva por solapamiento de filtros; reduce trades y mantiene neto positivo pequeño, útil para ranking exploratorio.

### COMB_008
- componentes: `EL_REPULSE_DIV` + `EL_Mogalef_Trend_Filter_V2` + `EL_NeutralZone_B_V2` + stop causal simple
- dataset: `MNQ 5m` práctico
- estado: `provisional_usable_for_ranking`
- interpretación breve: combinación triple ya usable para ranking, pero en esta muestra queda claramente débil y con neto negativo.

### COMB_009
- componentes: consenso `EL_STPMT_DIV` + `EL_REPULSE_DIV` + `EL_Mogalef_Trend_Filter_V2` + stop causal simple
- dataset: `MNQ 5m` práctico
- estado: `provisional_usable_for_ranking`
- interpretación breve: combinación de consenso muy restrictiva; produce pocas operaciones y en esta muestra no destaca.

### COMB_010
- componentes: `EL_STPMT_DIV` + `EL_NeutralZone_B_V2(use_as=signal)` + stop causal simple
- dataset: `MNQ 5m` práctico
- estado: `provisional_usable_for_ranking`
- interpretación breve: combinación ultra restrictiva por uso en modo señal de NeutralZone; casi no opera y no destaca en la muestra.

### COMB_011
- componentes: `EL_STPMT_DIV` + (`Trend_Filter_V2` OR `NeutralZone_B_V2(filter)`) + stop causal simple
- dataset: `MNQ 5m` práctico
- estado: `provisional_usable_for_ranking`
- interpretación breve: combinación más permisiva; aumenta frecuencia y mantiene neto positivo orientativo, útil para ranking exploratorio.

### COMB_012
- componentes: `EL_STPMT_DIV` + `Trend_Filter_V2` + `EL_NeutralZone_B_V2(signal)` + stop causal simple
- dataset: `MNQ 5m` práctico
- estado: `provisional_usable_for_ranking`
- interpretación breve: combinación extremadamente estricta; casi no genera operaciones y no aporta valor exploratorio visible en esta muestra.
