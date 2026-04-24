from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "EL_NeutralZone_B_V2.py"
spec = importlib.util.spec_from_file_location("neutralzone_b_v2", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules["neutralzone_b_v2"] = module
spec.loader.exec_module(module)
NeutralZoneBV2 = module.NeutralZoneBV2


def test_filter_mode_runs_and_emits_sentiment():
    close = [100, 101, 102, 103, 104, 103, 102, 101, 100, 99] * 30
    high = [c + 1 for c in close]
    low = [c - 1 for c in close]
    result = NeutralZoneBV2(use_as="filter", mme_period=5, ret_window=5, trend_indic_size=2).compute(high, low, close, 0.25)
    assert len(result.senti) == len(close)
    assert any(v in (0, 100) for v in result.senti)


def test_signal_mode_is_pulsed_not_persistent():
    close = [100, 101, 102, 103, 104, 105, 104, 103, 102, 101] * 30
    high = [c + 1 for c in close]
    low = [c - 1 for c in close]
    result = NeutralZoneBV2(use_as="signal", mme_period=5, ret_window=5, trend_indic_size=2).compute(high, low, close, 0.25)
    assert len(result.senti) == len(close)
    assert any(v in (0, 100) for v in result.senti)
    assert any(v == 50 for v in result.senti)


if __name__ == "__main__":
    test_filter_mode_runs_and_emits_sentiment()
    test_signal_mode_is_pulsed_not_persistent()
    print("ok")
