# EL_Mogalef_Trend_Filter_V2 - Ambigüedades abiertas

## 1. Índices negativos y orientación histórica
El fuente usa `[-i]` y `O[Length-i-1]`, una convención poco natural fuera de la plataforma original. Antes de Fase 2 habrá que fijar una traducción cronológica exacta para que el `open_shifted` apunte a la barra correcta.

## 2. Estado por defecto cuando `OffOn=0`
El bloque de interpretación no asigna explícitamente `sentiment=senti_pass` en todos los caminos cuando el filtro está apagado. La intención funcional parece ser dejar pasar, pero conviene confirmarlo en reconstrucción.

## 3. Caso `CAS=0` después de 2030
El código fuerza `CAS=0` si la fecha supera `05_12_2030`, pero no documenta por qué. Parece un kill-switch o caducidad. Debe preservarse como comportamiento observado, aunque quizá se parametrice al reconstruir.

## 4. Empates en la pendiente
Si un repulse no sube, cae automáticamente en `-1`. No existe estado plano. Esto puede meter ruido en zonas laterales; hay que mantenerlo literal salvo validación posterior.

## 5. Inicialización implícita de `sentiment`
En modo por lista de bloqueos, el fuente no siempre asigna `senti_pass` antes de probar casos bloqueados. En la plataforma original puede existir un valor previo por defecto. La implementación Python deberá inicializar explícitamente `pass/block` para evitar arrastre de estado.
