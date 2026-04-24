import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "EL_Mogalef_Trend_Filter_V2.py"
SPEC = spec_from_file_location("EL_Mogalef_Trend_Filter_V2", MODULE_PATH)
MODULE = module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

MogalefTrendFilterV2 = MODULE.MogalefTrendFilterV2


def _sample_ohlc(length=24):
    open_ = [100.0 + i for i in range(length)]
    high = [value + 2.0 for value in open_]
    low = [value - 2.0 for value in open_]
    close = [value + 1.0 for value in open_]
    return open_, high, low, close


def test_history_gate_keeps_cases_void_until_r3_times_five():
    open_, high, low, close = _sample_ohlc(24)
    indicator = MogalefTrendFilterV2(r1=1, r2=2, r3=3)

    result = indicator.compute(open_=open_, high=high, low=low, close=close)

    assert all(case is None for case in result.cases[:15])
    assert result.cases[15] is not None
    assert result.sentiment[14] == "block"


def test_monotonic_sample_maps_to_case_one_and_can_be_blocked():
    open_, high, low, close = _sample_ohlc(24)
    indicator = MogalefTrendFilterV2(r1=1, r2=2, r3=3, blocked_cases={1})

    result = indicator.compute(open_=open_, high=high, low=low, close=close)

    assert result.cases[15] == 1
    assert result.sentiment[15] == "block"


def test_trade_only_case_blocks_other_cases():
    open_, high, low, close = _sample_ohlc(24)
    indicator = MogalefTrendFilterV2(r1=1, r2=2, r3=3, trade_only_case=7)

    result = indicator.compute(open_=open_, high=high, low=low, close=close)

    assert result.cases[15] == 1
    assert result.sentiment[15] == "block"


def test_filter_off_returns_pass_on_valid_case():
    open_, high, low, close = _sample_ohlc(24)
    indicator = MogalefTrendFilterV2(r1=1, r2=2, r3=3, trade_only_case=7, off_on=0)

    result = indicator.compute(open_=open_, high=high, low=low, close=close)

    assert result.cases[15] == 1
    assert result.sentiment[15] == "pass"


def test_date_kill_switch_forces_case_zero_after_cutoff():
    open_, high, low, close = _sample_ohlc(24)
    dates = ["2030-12-04"] * 24
    dates[15] = "2030-12-06"
    indicator = MogalefTrendFilterV2(r1=1, r2=2, r3=3)

    result = indicator.compute(open_=open_, high=high, low=low, close=close, dates=dates)

    assert result.cases[15] == 0
    assert result.sentiment[15] == "pass"


def test_date_kill_switch_respects_trade_only_case_policy():
    open_, high, low, close = _sample_ohlc(24)
    dates = ["2030-12-04"] * 24
    dates[15] = "2030-12-06"
    indicator = MogalefTrendFilterV2(r1=1, r2=2, r3=3, trade_only_case=7)

    result = indicator.compute(open_=open_, high=high, low=low, close=close, dates=dates)

    assert result.cases[15] == 0
    assert result.sentiment[15] == "block"


if __name__ == "__main__":
    for test in (
        test_history_gate_keeps_cases_void_until_r3_times_five,
        test_monotonic_sample_maps_to_case_one_and_can_be_blocked,
        test_trade_only_case_blocks_other_cases,
        test_filter_off_returns_pass_on_valid_case,
        test_date_kill_switch_forces_case_zero_after_cutoff,
        test_date_kill_switch_respects_trade_only_case_policy,
    ):
        test()
    print("ok")
