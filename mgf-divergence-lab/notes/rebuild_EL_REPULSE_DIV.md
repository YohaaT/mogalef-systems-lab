PHASE: 2
OBJECTIVE: Reconstruir `EL_REPULSE_DIV` en Python reproducible.
SCOPE: Un componente. Sin QA formal en este run. Sin smoke formal en este run.
INPUTS: `PROJECT_MASTER.md`, `TOKEN_POLICY.md`, `RUN_PROTOCOL.md`, `mgf-control/phase_state.json`, `mgf-control/approval_queue.md`, `mgf-control/approval_request.md`, `mgf-control/session_checkpoint.md`, `mgf-control/night_run_summary.md`, `mgf-divergence-lab/spec/EL_REPULSE_DIV.md`, `mgf-divergence-lab/notes/EL_REPULSE_DIV_ambiguities.md`, `mgf-divergence-lab/repulse/EL_REPULSE_DIV.txt`.
EXPECTED ARTIFACT: `mgf-divergence-lab/src/EL_REPULSE_DIV.py`, `mgf-divergence-lab/tests/EL_REPULSE_DIV_test.py`, esta nota.
STOP CONDITION: detenerse al dejar la reconstrucción y tests mínimos persistidos.

## Resumen
Se creó una primera reconstrucción funcional de `EL_REPULSE_DIV` en Python con foco en reproducir:
- el cálculo autónomo de las tres curvas Repulse (`R1`, `R2`, `R3`);
- la detección retrospectiva de pivots altos y bajos por horizonte;
- divergencias normales alcistas y bajistas por horizonte;
- agregación secuencial a `Pose` y traducción a `sentiment`.

## Decisiones de traducción
- `ExpMovingAverage` se implementó como EMA estándar forward con inicialización en el primer valor disponible.
- El indexing retrospectivo del host (`O[Length-i-1]`, `serie[n]`) se trasladó a eje cronológico normal usando ventanas rolling y offsets explícitos.
- La detección de pivots conserva el caso especial de `smooth=1` presente en la fuente.
- Las líneas `Z*` se preservan como segmentos numéricos por barra de disparo para facilitar smoke o QA posterior, no como plotting host-equivalente.
- La caducidad artificial `if (date<01_01_2022)` no se trató como parte del núcleo funcional.
- El reescalado por `TickSize()` no se incorporó al núcleo porque en la spec quedó clasificado como visual.

## Riesgos conocidos
- La persistencia exacta de `Pose` en el host original puede diferir si la plataforma conserva el valor previo fuera del bloque visible.
- La equivalencia fina de EMA y pivots retrospectivos necesita contraste en re-QA.
- Aún no existe smoke formal con salidas multi-horizonte sobre series controladas.

Result:
Artifacts created:
- `mgf-divergence-lab/src/EL_REPULSE_DIV.py`
- `mgf-divergence-lab/tests/EL_REPULSE_DIV_test.py`
- `mgf-divergence-lab/notes/rebuild_EL_REPULSE_DIV.md`
Files read:
- `PROJECT_MASTER.md`
- `TOKEN_POLICY.md`
- `RUN_PROTOCOL.md`
- `mgf-divergence-lab/spec/EL_REPULSE_DIV.md`
- `mgf-divergence-lab/notes/EL_REPULSE_DIV_ambiguities.md`
- `mgf-divergence-lab/repulse/EL_REPULSE_DIV.txt`
- control files obligatorios
Scope respected: yes
Next recommended action: QA técnica breve de `EL_REPULSE_DIV`.
