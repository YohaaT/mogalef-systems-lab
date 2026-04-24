# COMB_001 Historical Baseline Documentation

## Qué recupera este archivo

`COMB_001_historical_baseline.py` recupera y verifica la combinación histórica que produjo los resultados orientativos antiguos del proyecto.

No redefine una estrategia nueva.
No reemplaza a `COMB_001.py` como baseline limpio.
Su función es preservar y validar la combinación histórica realmente usada para obtener:
- `97 trades`
- `17 wins`
- `80 losses`
- `1369.5 net points`

---

## Combinación histórica recuperada

La combinación histórica validada es:
- entrada: `EL_STPMT_DIV`
- filtro: `EL_Mogalef_Trend_Filter_V2`
- salida/riesgo: stop causal simple
- convención temporal: señal en `t`, entrada en apertura de `t+1`

Además, esta recuperación confirma que todos los trades del trade log histórico:
- respetan el lado de señal (`pose`)
- respetan el filtro (`sentiment = pass`)
- respetan la entrada en `t+1`
- respetan los precios de entrada documentados

---

## Qué no recupera todavía

Este runner no infiere todavía la lógica interna exacta de selección adicional que dejó fuera otras señales elegibles del dataset.

Por tanto, recupera con seguridad:
- la combinación histórica usada
- el resultado histórico persistido
- la coherencia del trade log histórico

Pero no prueba todavía la lógica completa del motor original que decidió por qué entraron exactamente esas 97 operaciones y no otras señales también válidas a simple vista.

---

## Interpretación correcta

A día de hoy quedan dos artefactos distintos:

### 1. `COMB_001.py`
Baseline limpio, reproducible y ejecutable hoy.

### 2. `COMB_001_historical_baseline.py`
Recuperación auditada de la combinación histórica que generó el baseline antiguo documentado.

La recomendación profesional es mantener ambos separados hasta reconstruir por completo la lógica exacta del runner histórico.
