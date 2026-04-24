import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "EL_Stop_Intelligent.py"
SPEC = spec_from_file_location("EL_Stop_Intelligent", MODULE_PATH)
MODULE = module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

StopIntelligent = MODULE.StopIntelligent


def test_initial_history_keeps_none_until_reference_volatility_exists():
    indicator = StopIntelligent(recent_volat=2, ref_volat=4)
    high = [14, 13, 12, 11, 10, 9]
    low = [10, 9, 8, 7, 6, 5]
    close = [12, 11, 10, 9, 8, 7]
    market_position = [1, 1, 1, 1, 1, 1]

    result = indicator.compute(high=high, low=low, close=close, market_position=market_position)

    assert result.avtrref[0] is not None
    assert result.avtrref[1] is not None
    assert result.avtrref[2] is None
    assert result.space[0] is not None
    assert result.space[1] is not None
    assert result.space[2] is None
    assert result.stop[4] is None
    assert result.stop[5] is None


def test_long_stop_does_not_move_away_once_it_has_tightened():
    indicator = StopIntelligent(quality=1, recent_volat=1, ref_volat=1, coef_volat=5, first_low_or_more=1)
    high = [10, 12, 11, 13, 12, 14, 13, 15]
    low = [8, 9, 7, 10, 9, 11, 10, 12]
    close = [9, 11, 10, 12, 11, 13, 12, 14]
    market_position = [1, 1, 1, 1, 1, 1, 1, 1]

    result = indicator.compute(high=high, low=low, close=close, market_position=market_position)

    active_stops = [value for value in result.stop if value is not None]
    assert len(active_stops) >= 2
    for earlier, later in zip(active_stops, active_stops[1:]):
        assert later >= earlier


def test_wait_for_xtrem_freezes_long_stop_until_breakout_occurs():
    indicator = StopIntelligent(
        quality=1,
        recent_volat=1,
        ref_volat=1,
        coef_volat=5,
        first_low_or_more=1,
        wait_for_xtrem=2,
    )
    high = [10, 13, 12, 14, 13, 13.5, 13.6, 15]
    low = [8, 9, 7, 10, 9, 10.5, 10.6, 12]
    close = [9, 12, 11, 13, 12, 12.8, 12.9, 14]
    market_position = [1, 1, 1, 1, 1, 1, 1, 1]

    result = indicator.compute(high=high, low=low, close=close, market_position=market_position)

    frozen_idx = 1
    assert result.hh0[frozen_idx + 1] is not None
    assert high[frozen_idx] <= result.hh0[frozen_idx + 1]
    assert result.stop[frozen_idx] == result.stop[frozen_idx + 1]


if __name__ == "__main__":
    for test in (
        test_initial_history_keeps_none_until_reference_volatility_exists,
        test_long_stop_does_not_move_away_once_it_has_tightened,
        test_wait_for_xtrem_freezes_long_stop_until_breakout_occurs,
    ):
        test()
    print("ok")
