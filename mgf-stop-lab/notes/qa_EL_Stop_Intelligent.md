# QA EL_Stop_Intelligent

PHASE: 2
OBJECTIVE: Ejecutar una QA técnica breve únicamente sobre `EL_Stop_Intelligent`.
SCOPE: Un solo componente. Sin fixes en este run, sin smoke test, sin backtest, sin tocar otros componentes.
INPUTS: PROJECT_MASTER.md, TOKEN_POLICY.md, RUN_PROTOCOL.md, `mgf-stop-lab/spec/EL_Stop_Intelligent.md`, `mgf-stop-lab/src/EL_Stop_Intelligent.py`, `mgf-stop-lab/tests/EL_Stop_Intelligent_test.py`, `mgf-stop-lab/notes/rebuild_EL_Stop_Intelligent.md`, `mgf-stop-lab/intelligent-family/EL_Stop_Intelligent.txt`.
EXPECTED ARTIFACT: `mgf-stop-lab/notes/qa_EL_Stop_Intelligent.md`.
STOP CONDITION: detenerse al guardar el dictamen de QA.

## Resultado
Dictamen del componente: `FIX`.

## Hallazgo 1, el test file no es ejecutable tal como está
El archivo `mgf-stop-lab/tests/EL_Stop_Intelligent_test.py` carga el módulo con `module_from_spec(...)` y `exec_module(...)`, pero no registra antes el módulo en `sys.modules`.

Con esta combinación, Python 3.8 falla al evaluar `@dataclass` en `EL_Stop_Intelligent.py` con:
- `AttributeError: 'NoneType' object has no attribute '__dict__'`

Eso deja la suite rota antes de empezar a validar la lógica funcional.

## Hallazgo 2, el primer test tiene una expectativa incompatible con la implementación actual
Forzando una carga correcta del módulo para poder inspeccionar la lógica, el test:
- `test_initial_history_keeps_none_until_reference_volatility_exists`

falla en:
- `assert result.space[3] is not None`

La implementación devuelve `None` en `space[3]` para esa muestra corta. Con la orientación cronológica usada en el rebuild y la ventana `ref_volat=4`, esa expectativa no queda demostrada por el caso de prueba actual.

## Comprobaciones que sí pasaron tras carga controlada
- `test_long_stop_does_not_move_away_once_it_has_tightened`
- `test_wait_for_xtrem_freezes_long_stop_until_breakout_occurs`

## Evaluación técnica
No apareció en esta QA evidencia suficiente de bug claro en el núcleo del stop.
El estado `FIX` se debe, de forma concreta, a que:
1. la suite actual no arranca limpia por un problema de importación del test;
2. uno de los tests codifica una expectativa que no queda alineada con el comportamiento observado del rebuild.

## Acción mínima recomendada
Abrir un run de corrección únicamente para:
1. arreglar la carga del módulo en `mgf-stop-lab/tests/EL_Stop_Intelligent_test.py`;
2. rediseñar o corregir el test de historia inicial para que valide el punto exacto donde `avtrref` y `space` deben empezar a existir bajo la orientación elegida.

## Qué no se hizo
- No se modificó código.
- No se modificaron tests.
- No se hizo smoke test.
- No se hizo backtest.
- No se abrió `Fase 3`.

Result:
Artifacts created:
- `mgf-stop-lab/notes/qa_EL_Stop_Intelligent.md`
Files read:
- PROJECT_MASTER.md
- TOKEN_POLICY.md
- RUN_PROTOCOL.md
- `mgf-stop-lab/spec/EL_Stop_Intelligent.md`
- `mgf-stop-lab/src/EL_Stop_Intelligent.py`
- `mgf-stop-lab/tests/EL_Stop_Intelligent_test.py`
- `mgf-stop-lab/notes/rebuild_EL_Stop_Intelligent.md`
- `mgf-stop-lab/intelligent-family/EL_Stop_Intelligent.txt`
Scope respected: yes
Next recommended action: run de corrección solo sobre `EL_Stop_Intelligent_test.py` y su caso de historia inicial.