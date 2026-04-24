from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from EL_REPULSE_DIV import _compute_horizon_divergences, _repulse_series, compute_el_repulse_div


def test_returns_expected_keys_and_lengths():
    open_ = [100 + (i % 7) for i in range(120)]
    high = [o + 3 + (i % 3) for i, o in enumerate(open_)]
    low = [o - 3 for o in open_]
    close = [l + ((h - l) * 0.6) for h, l in zip(high, low)]

    out = compute_el_repulse_div(open_=open_, high=high, low=low, close=close)

    expected = {
        "INDICM",
        "INDICA",
        "INDICB",
        "DIVHM",
        "DIVBM",
        "DIVHA",
        "DIVBA",
        "DIVHB",
        "DIVBB",
        "ZBM",
        "ZHM",
        "ZBA",
        "ZHA",
        "ZBB",
        "ZHB",
        "Pose",
        "sentiment",
    }
    assert expected == set(out.keys())
    for key in expected:
        assert len(out[key]) == len(close)


def test_repulse_series_produces_finite_values_after_warmup():
    open_ = [100 + ((i * 5) % 9) for i in range(160)]
    high = [o + 4 + (i % 4) for i, o in enumerate(open_)]
    low = [o - 4 - (i % 2) for i, o in enumerate(open_)]
    close = [l + ((h - l) * 0.55) for h, l in zip(high, low)]

    out = _repulse_series(open_, high, low, close, length=5)
    tail = [v for v in out[-40:] if v is not None]

    assert tail
    assert all(isinstance(v, float) for v in tail)


def test_detects_bearish_divergence_on_short_horizon_with_smooth_1():
    indic = [70.0, 10.0, 70.0, 30.0, 80.0, 60.0, 40.0, 0.0, 10.0, 40.0, 0.0, 0.0]
    high = [108.0, 112.0, 116.0, 118.0, 122.0, 112.0, 114.0, 103.0, 123.0, 108.0, 111.0, 109.0]
    low = [93.0, 104.0, 102.0, 112.0, 117.0, 106.0, 105.0, 94.0, 110.0, 98.0, 105.0, 96.0]
    close = [98.23, 110.95, 102.49, 114.05, 117.82, 108.62, 106.96, 102.86, 112.77, 106.92, 106.39, 96.93]

    out = _compute_horizon_divergences(
        indic=indic,
        high=high,
        low=low,
        close=close,
        smooth_high=1,
        smooth_low=1,
        active=True,
        bull_value=0.4,
        bear_value=-0.4,
    )

    assert out["bear"][10] == -0.4


def test_detects_bullish_divergence_on_short_horizon_with_smooth_1():
    indic = [10.0, 50.0, 80.0, 70.0, 80.0, 0.0, 20.0, 50.0, 50.0, 40.0, 70.0, 80.0]
    high = [100.0, 104.0, 121.0, 118.0, 111.0, 122.0, 117.0, 118.0, 105.0, 108.0, 108.0, 108.0]
    low = [84.0, 101.0, 104.0, 80.0, 93.0, 84.0, 92.0, 92.0, 103.0, 83.0, 96.0, 100.0]
    close = [86.0, 102.0, 110.0, 82.0, 95.0, 86.0, 94.0, 95.0, 104.0, 84.0, 98.0, 101.0]

    out = _compute_horizon_divergences(
        indic=indic,
        high=high,
        low=low,
        close=close,
        smooth_high=1,
        smooth_low=1,
        active=True,
        bull_value=0.4,
        bear_value=-0.4,
    )

    assert out["bull"][10] == 0.4


if __name__ == "__main__":
    test_returns_expected_keys_and_lengths()
    test_repulse_series_produces_finite_values_after_warmup()
    test_detects_bearish_divergence_on_short_horizon_with_smooth_1()
    test_detects_bullish_divergence_on_short_horizon_with_smooth_1()
    print("ok")
