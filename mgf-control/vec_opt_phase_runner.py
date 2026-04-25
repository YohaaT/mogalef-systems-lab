"""Run existing POOL phase scripts with vec_optimized strategy modules.

The legacy phase scripts import canonical module names at top level.  To keep
those files untouched, this runner injects optimized modules into ``sys.modules``
before executing the target script with ``runpy``.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import COMB_001_TREND_V1_vec_optimized as comb001_vec
import COMB_002_IMPULSE_V2_vec_optimized as comb002_vec


def run_phase_script(script_name: str) -> None:
    script_path = Path(__file__).with_name(script_name)
    if not script_path.exists():
        raise FileNotFoundError(script_path)

    sys.modules["COMB_001_TREND_V1"] = comb001_vec
    sys.modules["COMB_002_IMPULSE_V2_adaptive"] = comb002_vec
    runpy.run_path(str(script_path), run_name="__main__")

