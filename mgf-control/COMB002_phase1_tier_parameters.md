# COMB002 Phase 1 Tier Parameters

Source of truth:
- Contract-active Phase 1 on `friday_to_expiry_week_monday`
- Timezone logic: `Europe/Madrid`
- Context only blocks entries; indicators are computed on the full contract series

This file groups the current Phase 1 winners into tiers for later C# porting.

## Tier 1

### ES 15m
- Horario: `asiatico`
- Filtro diario: `no_mardi`
- Horario Madrid: `23:00-08:00`
- PF: `1.291687`
- Equity points: `409.767857`
- Max DD: `75.866071`
- Trades: `559`

### ES 5m
- Horario: `asiatico`
- Filtro diario: `no_mardi`
- Horario Madrid: `23:00-08:00`
- PF: `1.223796`
- Equity points: `591.517857`
- Max DD: `113.607143`
- Trades: `2047`

## Tier 2

### ES 10m
- Horario: `asiatico`
- Filtro diario: `no_lundi_mardi`
- Horario Madrid: `23:00-08:00`
- PF: `1.088302`
- Equity points: `133.366071`
- Max DD: `145.410714`
- Trades: `746`

### FDAX 15m
- Horario: `asiatico`
- Filtro diario: `no_lundi`
- Horario Madrid: `23:00-08:00`
- PF: `1.257061`
- Equity points: `1188.357143`
- Max DD: `333.071429`
- Trades: `375`

## Tier 3

### FDAX 5m
- Horario: `asiatico`
- Filtro diario: `no_lundi`
- Horario Madrid: `23:00-08:00`
- PF: `1.117723`
- Equity points: `1008.000000`
- Max DD: `394.607143`
- Trades: `1246`

### NQ 5m
- Horario: `asiatico`
- Filtro diario: `no_lundi_mardi`
- Horario Madrid: `23:00-08:00`
- PF: `1.154113`
- Equity points: `1157.330357`
- Max DD: `484.964286`
- Trades: `1495`

## Tier 4

### NQ 15m
- Horario: `madrid_1400_2145`
- Filtro diario: `no_lundi`
- Horario Madrid: `14:00-21:45`
- PF: `1.396342`
- Equity points: `4915.660714`
- Max DD: `840.500000`
- Trades: `710`

## Notes for the C# port

- Keep the tier order above as the priority list for later implementation.
- Do not re-optimize the indicator math when porting.
- Preserve the same timezone conversion and day-of-week logic.
- Preserve the same contract-active rollover methodology.
- Phase 2 should start from the winner context of each dataset, unless the workflow is later expanded to sweep all `PF > 1.0` Phase 1 contexts.
