# Notas Extraídas — "Trading Automatique: Conception et Sécurisation"
# Eric LEFORT (Mogalef-Trading.com) — 52 páginas
# Extraído: 2026-04-22 — NO RELEER EL PDF, usar este documento

---

## 1. ACTIVO Y TEMPORALIDAD

- **Ejemplo del PDF**: DOW JONES → equivalente NT8: **YM (E-mini Dow futures)**
- **Temporalidad**: **5 minutos** (pág 7: "Ici la courbe de gain en 5mn avec un TimeStop à 10 bougies")
- Por qué DOW:
  - Valor elevado → movimientos de gran amplitud
  - Spread muy pequeño (uno de los más pequeños del mercado)
  - Slippage quasi negligible
  - Sesgo direccional alcista → ligera ventaja en trading unidireccional

---

## 2. SEÑAL DE ENTRADA

- **Señal base**: Cassure haussière inclinée (ruptura alcista inclinada)
  - "Cassures baissières inclinées donnent le meilleur résultat" — usar roturas inclinadas, no planas
  - Las cassures horizontales ("à plat") → NO recomendadas (pág 8: "Pas très engageant!")
- **En nuestro sistema**: usamos EL_STPMT_DIV como señal (alternativa válida, señal de divergencia)
- **Pre-selección de trades**: usar TimeStop=10 primero para identificar trades que "parten bien", luego decidir tendance vs impulsion

---

## 3. TIPOS DE SISTEMA (misma señal, dos configuraciones)

| | **COMB_001 — TENDANCE** | **COMB_002 — IMPULSION** |
|---|---|---|
| TimeStop | **30+** bougies | **15** bougies |
| Profit Target | 10 ATR | 10 ATR |
| Stop suiveur | **Stop Intelligent** | **SuperStop Long** |
| Salida extra | — | **Intelligent Scalping Target** |
| MTF Trend Filter | Opcional (leve mejora) | **NO — no aporta nada** |
| Filtro volatilidad | **SÍ** | **NO — amputa gain y regularidad** |
| Filtro horario | **SÍ — IMPERATIVO** | **SÍ — IMPERATIVO** |
| Filtro diario | **SÍ** (no mardi) | **SÍ** (no mardi) |

---

## 4. FILTROS

### 4.1 Filtro Horario (pág 11) — "À garder impérativement"
- Operar de **9h a 17h** Y de **20h a 22h**
- Elimina la noche y algunas horas desfavorables
- **CRÍTICO**: en nuestro sistema solo teníamos 12-15 UTC → falta la franja 20-22

### 4.2 Filtro Diario (pág 12) — "À garder"
- **No operar el MARTES** (prioridad máxima)
- **No operar el LUNES** (segunda prioridad)
- Elimina solo 1-2 días → poco riesgo de sobreoptimización
- En optimización: testar `all` / `no_mardi` / `no_lundi` / `no_lundi_mardi`

### 4.3 Force Relative (pág 13-14) — **ELIMINAR**
- "N'apporte rien, à éliminer"
- Comparación DOW vs SP500: reduce trades sin mejorar suficiente
- Comparación DOW vs CAC: no mejora nada
- **Nunca incluir en nuestros sistemas**

### 4.4 MTF Trend Filter — "Mogalef Trend Filter" (pág 16)
- Para TENDANCE: mejora gain medio por trade + rendimiento total (mantener)
- Para IMPULSION: "Le MTF n'apporte rien" — no incluir en COMB_002

### 4.5 Filtro Volatilidad ATR (pág 17)
- Para TENDANCE: 
  - Elimina periodos de muy baja y muy alta volatilidad
  - Dobla el trade medio
  - Reduce 25% el número de trades
  - Aumenta regularidad de la curva → **MANTENER en COMB_001**
- Para IMPULSION:
  - "Le filtre de volatilité ampute gain et régularité" — **ELIMINAR en COMB_002**

---

## 5. SALIDAS (EXITS)

### Evaluadas en el PDF (pág 20-26):

| Salida | Resultado | Usar |
|---|---|---|
| Profit Target = f(volatilidad) → 10 ATR | Sube regularidad, techo en 10 ATR | ✅ AMBOS |
| Divergencia MACD inversa | Apport moderado, baja pérdida media | Opcional |
| Sobrecompra Estocástico | "Apport nul, à éviter" | ❌ NUNCA |
| **Intelligent Scalping Target** | SOLO para impulsion (7-20 bougies) | ✅ COMB_002 únicamente |

### Intelligent Scalping Target (pág 25, 36):
- Diseñado para trades 7-20 bougies
- NO apto para trading de tendencia
- Para impulsion: "fait presque tout, tout seul" — es el componente principal
- Reduce trade medio, pero mucha proporción de ganadores
- Mejora regularidad de curva enormemente
- **Motor principal de COMB_002**

### TimeStop final:
- No fijar TimeStop hasta definir stops (pág 27): "il vaut mieux attendre car certains stops sont conçus pour les tendances"

---

## 6. STOPS

### 6.1 Stop Intelligent (pág 29) — Para TENDANCE
- "Convient au travail de tendance"
- Reduce fuertemente el trade perdedor medio
- Aumenta mucho la regularidad del gain
- **Usar en COMB_001_TREND**

### 6.2 Stop Long Life / Dernier Bas (pág 30) — Para TENDANCE (Pascal Hirtz)
- Convient au trading de tendance
- Aumenta fuertemente el "gain moyen / perte moyenne"
- Pero aumenta poco la regularidad
- Alternativa al Stop Intelligent (no implementado en nuestro lab)

### 6.3 SuperStop Long (pág 31) — Para IMPULSION
- "Convient au trading d'impulsion"
- Aumenta fuertemente la regularidad (Perf/perte cumulée)
- Disminuye el trade perdedor medio
- En test de impulsion: "placé loin donc presque inefficace, SAUF pour la perte maximum cumulée qu'il réduit sérieusement — on doit le garder"
- **Usar en COMB_002_IMPULSE** — principalmente como protección de DD

### Stop de Seguridad y Money Management (pág 39):
- "Ne doit pas ou très peu interférer avec les résultats du système"
- Determinar DESPUÉS de que el sistema esté completo
- "Plus on rapproche ce stop, plus il dégrade le système"
- **Regla**: colocar tan lejos como sea razonable

---

## 7. COMPOSICIÓN FINAL DE CADA SISTEMA

### COMB_001_TREND (pág 33):
```
+ Filtro volatilidad (ATR range)
+ Filtro tendencia MTF (opcional, leve mejora)
+ Profit Target 10 ATR
+ Stop Intelligent
+ TimeStop 30
+ Filtro horario (9-17 + 20-22)
+ Filtro diario (no mardi)
```

### COMB_002_IMPULSE — CONFIGURACIÓN FINAL CORREGIDA (pág 34-36):
```
- NO filtro volatilidad (amputa performance)
- NO MTF Trend Filter (no aporta nada)
+ Filtro horario (9-17 + 20-22) — SOLO filtros temporales
+ Filtro diario (no mardi)
+ Profit Target 10 ATR
+ SuperStop Long (protege DD máximo)
+ Intelligent Scalping Target (motor principal)
+ TimeStop 15
```

---

## 8. VALIDACIÓN OUT-OF-SAMPLE (pág 37-38)

### Regla clave:
> "Il faut tester sur un historique correspondant à la situation pendant la période de test, et surtout correspondant à la période à venir!"

- Datos de GUERRA (feb 2022 - may 2023) ≠ datos de COVID → no mezclar para validación
- Validar siempre en datos del **mismo régimen de mercado**
- Nuestro protocolo: Phase A (60% train) + Phase B (40% unseen) del mismo periodo ✅

### Lo que NO hacer jamás (pág 38):
> "Ne surtout pas chercher à optimiser de nouveau les paramètres de l'indicateur, des stops, objectifs, filtres…"
> "Ceci conduirait sans aucun doute à une sur-optimisation fatale"

---

## 9. CAPITAL REQUERIDO (pág 40, 44)

### Sistema solo:
| Métrica | TENDANCE | IMPULSION |
|---|---|---|
| Max loss ≤ 10% capital | 34 000€ (DD=3400) | 28 500€ (DD=2850) |
| Max trade ≤ 1% capital | 118 000€ | 115 000€ |

### Combinado (4 sistemas, pág 43-44):
- DOW Tendances: Perf/perte cumulée=58, Max DD=2440
- DOW Impulsions: Perf/perte cumulée=55, Max DD=2600
- Capital combinado: Tendance=24 400€, Impulsion=26 000€

### Cita clave:
> "Le secret de la sécurité: Utiliser plusieurs systèmes — sur des supports différents, de conception différente, sur des unités de temps différentes."

---

## 10. REDUCCIÓN DE RIESGO — PORTAFOLIO (pág 41)

Para reducir riesgo usar múltiples sistemas:
1. **Sobre subyacentes diferentes** (no correlacionados si mismo tipo)
2. **De concepción diferente** (tendance + impulsion + breakout…)
3. **En unidades de tiempo diferentes** (5m + 15m + 1h…)

Combinar resultados para que periodos perdedores de cada sistema sean compensados por periodos ganadores de los otros.

> "Aucun système n'étant éternel, il vous faudra sans arrêt en chercher de nouveaux pour remplacer ceux qui faiblissent."

---

## 11. PLATAFORMA ORIGINAL (pág 48)

- Mogalef usó **NanoTrader** (WHSelfinvest) con **MetaSentimentor**
- Nosotros portamos a **NinjaTrader 8** (NT8) → equivalencias ya implementadas
- MetaSentimentor = cerebro de la plataforma; en NT8 usamos lógica booleana directa

---

## 12. NOTAS DE IMPLEMENTACIÓN PARA NOSOTROS

### Señal cassure vs STPMT_DIV:
- El PDF usa Cassure Haussière como señal de entrada
- Nosotros usamos EL_STPMT_DIV (divergencia) → señal diferente pero igualmente válida dentro de la metodología
- Mantener STPMT_DIV como está (ya optimizado en Phase 1)

### Filtro horario corregido:
- PDF: 9h-17h + 20h-22h (hora France / CET = UTC+1 en invierno, UTC+2 en verano)
- En datos YM (US Eastern): CET 9h = ET 3h; CET 20h = ET 14h
- **Perfiles a testar en Phase 2b**:
  - `[9..17 CET]` = `[8..16 UTC]` aprox
  - `[9..17 + 20..22 CET]` = `[8..16 + 19..21 UTC]` aprox
  - `[12..15 UTC]` (nuestro previo — solo sesión US tarde)
  - `[8..21 UTC]` (franja amplia)

### SuperStop — spec disponible:
- `mgf-stop-lab/super-stop/Super_Stop_Long.txt`
- `mgf-stop-lab/super-stop/Super_Stop_Long_5beta.txt`
- Hay versión 5beta → usar esa (más reciente)

### Intelligent Scalping Target — spec NO encontrada en repositorio:
- No existe en `raw_material/` ni en ningún `.txt`
- Buscar en archivos NanoTrader `.txt` disponibles en `Desktop/Mogalef/`
- Alternativamente: definir como "objetivo dinámico corto basado en ATR reciente"

---

*Documento generado 2026-04-22 — Fuente: PDF 52 págs completo extraído con PyMuPDF*
