PHASE: 2
OBJECTIVE: Reconstruir `EL_STPMT_DIV` en Python reproducible.
SCOPE: Un componente. Sin QA formal en este run. Sin smoke formal en este run.
INPUTS: `PROJECT_MASTER.md`, `TOKEN_POLICY.md`, `RUN_PROTOCOL.md`, `mgf-control/phase_state.json`, `mgf-control/approval_queue.md`, `mgf-control/approval_request.md`, `mgf-control/session_checkpoint.md`, `mgf-control/night_run_summary.md`, `mgf-control/workflow_operating_mode.md`, `mgf-divergence-lab/spec/EL_STPMT_DIV.md`, `mgf-divergence-lab/notes/EL_STPMT_DIV_ambiguities.md`, `mgf-divergence-lab/stpmt/EL_STPMT_DIV.txt`.
EXPECTED ARTIFACT: `mgf-divergence-lab/src/EL_STPMT_DIV.py`, `mgf-divergence-lab/tests/EL_STPMT_DIV_test.py`, esta nota.
STOP CONDITION: detenerse al dejar la reconstrucción y tests mínimos persistidos.

## Resumen
Se creó una primera reconstrucción funcional de `EL_STPMT_DIV` en Python con foco en reproducir:
- la STPMT interna de 4 ventanas;
- la detección de pivots altos y bajos;
- divergencias normales e inversas;
- `pose` y `sentiment`.

## Decisiones de traducción
- `MovingAverage` se implementó provisionalmente como SMA simple, coherente con la spec y pendiente de QA específica.
- El núcleo se implementó en eje cronológico normal, sin reproducir literalmente el indexing negativo del host.
- La detección de pivots se reconstruyó respetando la lógica de confirmación retrospectiva, pero con helpers forward-only y validación pendiente de alineación fina.
- Las líneas `Z*` se guardan como segmentos retrospectivos por barra de disparo, solo como artefacto estructural para smoke/QA, no como plotting host-equivalente.
- La caducidad por fecha `date<01_01_2030` no se portó como lógica funcional.
- Alertas, popup, sound, email y filtro horario quedaron fuera del núcleo de cálculo y se preservaron solo vía `pose`/`sentiment`.

## Riesgos conocidos
- El comportamiento del host en primeras barras sigue necesitando contraste adicional en re-QA.
- Aún no existe smoke formal con casos diseñados para divergencia real.

## Fix aplicado en 2026-04-15 09:29 UTC run
- Se corrigió la traducción de `temp2=temp1[$SmoothH]` para pivots altos y de `temp5=temp4[$SmoothB]` para pivots bajos. Antes se estaba desplazando dos veces el índice, lo que podía desalinear la confirmación retrospectiva del pivot.
- Se extrajo la lógica de divergencias a un helper interno reutilizable para poder validarla con series sintéticas controladas sin depender del calentamiento completo de la STPMT.
- Se añadieron tests dirigidos para `smooth=1` con disparo explícito de divergencia bajista normal y alcista normal, incluyendo validación de `pose` y `sentiment`.

Result:
Artifacts created:
- `mgf-divergence-lab/src/EL_STPMT_DIV.py`
- `mgf-divergence-lab/tests/EL_STPMT_DIV_test.py`
- `mgf-divergence-lab/notes/rebuild_EL_STPMT_DIV.md`
Files read:
- `mgf-divergence-lab/spec/EL_STPMT_DIV.md`
- `mgf-divergence-lab/notes/EL_STPMT_DIV_ambiguities.md`
- `mgf-divergence-lab/stpmt/EL_STPMT_DIV.txt`
- control files obligatorios
Scope respected: yes
Next recommended action: QA técnica breve de `EL_STPMT_DIV`.
