# EL_REPULSE_DIV ambiguities

## 1. Variante no idéntica a WHS
La fuente declara explícitamente que esta versión es válida pero no coincide exactamente con el Repulse de WHS.

Implicación:
- la referencia canónica para el lab debe ser este código local, no una implementación externa de Repulse aparentemente estándar.

## 2. Índices retrospectivos y acceso a `open[L-1]`
El código usa expresiones del tipo `O[Length1-i-1]` dentro de bucles retrospectivos.

Ambigüedad:
- al portar a Python hay que fijar con precisión la equivalencia entre ese indexing y una implementación forward con ventanas rolling.

Impacto:
- un desfase de una barra alteraría el valor del Repulse y, por arrastre, los pivots y divergencias.

## 3. Detección de pivots usando close en vez de high/low
Para confirmar pivots actuales, la lógica usa condiciones sobre `close` (`c<=c[1]` o `c>=c[1]`) y no sobre `high`/`low`.

Ambigüedad:
- no está documentado por qué se usa close como filtro de giro inmediato mientras el precio asociado del pivot usa `Highest` o `Lowest`.

Decisión provisional:
- preservar la lógica tal cual porque parece intencional.

## 4. Prioridad real entre horizontes
La señal final revisa primero Repulse corto, luego medio, luego largo.

Ambigüedad:
- no está escrito como regla doctrinal, pero en la práctica el orden del código define prioridad si varios horizontes disparan simultáneamente.

## 5. Persistencia de `Pose`
Dentro del bucle de duración, `Pose` solo se actualiza si todavía no es `1` ni `-1`.

Ambigüedad:
- no se resetea explícitamente al inicio de cada barra en el fragmento visible.

Impacto:
- el host puede estar aplicando semántica de serie persistente que mantenga el último valor, lo cual afecta cuántas barras dura realmente una señal.

## 6. Reescalado visual posterior a la señal
Las series `DIV*` se reescalan con `TickSize()` después de usarse para activar `Pose`.

Ambigüedad:
- parece una operación puramente visual para plot, pero debe confirmarse al reconstruir para no confundir marcador gráfico con lógica de señal.

## 7. Caducidad por fecha
El núcleo de divergencias está envuelto por `if (date<01_01_2022)`.

Ambigüedad:
- esto parece una protección temporal o expiración artificial, no parte del modelo de trading.

Decisión provisional:
- no tratar esta fecha como parte de la lógica funcional de negocio.

## 8. Tipo exacto de EMA
La función usada es `ExpMovingAverage`.

Ambigüedad:
- conviene confirmar si el host usa la convención EMA estándar o una inicialización particular en primeras barras.

## 9. Ausencia de divergencias inversas
A diferencia de `EL_STPMT_DIV`, aquí solo se modelan divergencias normales.

Ambigüedad:
- no se sabe si es una decisión conceptual del componente o una simplificación de esta variante.

Implicación:
- no extrapolar capacidades de `EL_REPULSE_DIV` desde otros módulos de divergencia.
