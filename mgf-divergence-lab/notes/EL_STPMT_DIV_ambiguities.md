# EL_STPMT_DIV ambiguities

## 1. Construcción retrospectiva con índices negativos
La fuente calcula gran parte de la STPMT con bucles `for i=0 to FinalBarIndex()` y asignaciones `serie[-i]`.

Ambigüedad:
- no queda completamente especificado cómo replica el motor el orden exacto de evaluación retrospectiva frente a una implementación Python forward-only.

Impacto:
- puede cambiar los primeros valores válidos y algunos pivots iniciales.

## 2. Ventanas exactas de la STPMT
La fuente usa ventanas implícitas de 5, 14, 45 y 75 barras para máximos y mínimos, pero luego asigna dos referencias visuales `k=40` y `kk=52` sin documentarlas.

Ambigüedad:
- `k` y `kk` parecen niveles visuales, no parte de la lógica de señal.

Decisión provisional:
- tratarlos como overlays visuales, no como inputs funcionales.

## 3. Tipo exacto de media móvil
La fuente usa `MovingAverage` para `Stod1..4` y `MA`.

Ambigüedad:
- no se aclara si `MovingAverage` equivale a SMA simple en todos los hosts o a otra variante por defecto.

Impacto:
- una diferencia pequeña en suavizado puede mover pivots y divergencias.

## 4. Semántica exacta de divergencia normal e inversa
El selector `$ONone1Normals2Inverses3All` activa cuatro familias de divergencia.

Ambigüedad:
- el naming interno es claro, pero la terminología operativa exacta de “inversa” no está documentada fuera del patrón de comparación entre pivots.

Decisión provisional:
- preservar la definición literal del código como referencia canónica.

## 5. Resolución de conflictos entre señales opuestas
`pose` se asigna secuencialmente:
- primero por `DIVH`
- luego por `DIVB`
- luego por `DIVHI`
- luego por `DIVBI`

Ambigüedad:
- si coexistieran señales opuestas en la misma barra desplazada, la última evaluación podría sobrescribir la anterior.

Impacto:
- la prioridad real es procedural, no declarativa.

## 6. Filtro temporal
El horario `$StartTime/$EndTime` solo se aplica en `interpretation`, no en el cálculo bruto de divergencias.

Ambigüedad:
- no está claro si fuera de horario la intención es bloquear la señal o solo bloquear alertas y sentimiento final.

Decisión provisional:
- la señal interna existe siempre; el filtro horario solo condiciona la capa de interpretación/alerta.

## 7. Caducidad por fecha
El bloque principal está envuelto por `if (date<01_01_2030)`.

Ambigüedad:
- esto parece un vencimiento deliberado o una protección temporal, no parte de la lógica de trading.

Decisión provisional:
- no tratarlo como lógica funcional del componente al reconstruir la especificación.

## 8. Uso de highs/lows para una STPMT “tipo STO”
El comentario inicial dice que esta versión mira high y low para un indicador de tipo estocástico.

Ambigüedad:
- no queda explícito si existe otra versión base basada en close-only o en otro rango.

Impacto:
- la comparación futura con otras variantes debe hacerse con cuidado.
