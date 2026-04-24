from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from EL_STPMT_DIV import _compute_divergences_from_indicator, compute_el_stpmt_div


def test_returns_expected_keys_and_lengths():
    high = [10 + (i % 5) for i in range(140)]
    low = [h - 3 for h in high]
    close = [l + 1.5 for l in low]

    out = compute_el_stpmt_div(high=high, low=low, close=close)

    expected = {
        "INDIC",
        "MA",
        "Stod1",
        "Stod2",
        "Stod3",
        "Stod4",
        "DIVH",
        "DIVB",
        "DIVHI",
        "DIVBI",
        "pose",
        "sentiment",
        "ZB",
        "ZH",
        "ZBI",
        "ZHI",
    }
    assert expected == set(out.keys())
    for key in expected:
        assert len(out[key]) == len(close)


def test_stpmt_produces_finite_values_after_warmup():
    high = [100 + ((i * 7) % 11) for i in range(180)]
    low = [h - 6 - (i % 3) for i, h in enumerate(high)]
    close = [l + ((h - l) * 0.6) for h, l in zip(high, low)]

    out = compute_el_stpmt_div(high=high, low=low, close=close)
    indic_tail = [v for v in out["INDIC"][-40:] if v is not None]

    assert indic_tail
    assert all(isinstance(v, float) for v in indic_tail)


def test_detects_bearish_divergence_and_sell_pose_with_smooth_1():
    indic = [70.0, 10.0, 70.0, 30.0, 80.0, 60.0, 40.0, 0.0, 10.0, 40.0, 0.0, 0.0]
    high = [108.0, 112.0, 116.0, 118.0, 122.0, 112.0, 114.0, 103.0, 123.0, 108.0, 111.0, 109.0]
    low = [93.0, 104.0, 102.0, 112.0, 117.0, 106.0, 105.0, 94.0, 110.0, 98.0, 105.0, 96.0]

    out = _compute_divergences_from_indicator(
        indic=indic,
        high=high,
        low=low,
        mode=1,
        decal_entry=0,
        smooth_h=1,
        smooth_b=1,
        distance_max_h=200,
        distance_max_l=200,
    )

    assert out["DIVB"][10] == -3.0
    assert out["pose"][10] == -1
    assert out["sentiment"][10] == 0


def test_detects_bullish_divergence_and_buy_pose_with_smooth_1():
    indic = [10.0, 50.0, 80.0, 70.0, 80.0, 0.0, 20.0, 50.0, 50.0, 40.0, 70.0, 80.0]
    high = [100.0, 104.0, 121.0, 118.0, 111.0, 122.0, 117.0, 118.0, 105.0, 108.0, 108.0, 108.0]
    low = [84.0, 101.0, 104.0, 80.0, 93.0, 84.0, 92.0, 92.0, 103.0, 83.0, 96.0, 100.0]

    out = _compute_divergences_from_indicator(
        indic=indic,
        high=high,
        low=low,
        mode=1,
        decal_entry=0,
        smooth_h=1,
        smooth_b=1,
        distance_max_h=200,
        distance_max_l=200,
    )

    assert out["DIVH"][10] == 3.0
    assert out["pose"][10] == 1
    assert out["sentiment"][10] == 100


if __name__ == "__main__":
    test_returns_expected_keys_and_lengths()
    test_stpmt_produces_finite_values_after_warmup()
    test_detects_bearish_divergence_and_sell_pose_with_smooth_1()
    test_detects_bullish_divergence_and_buy_pose_with_smooth_1()
    print("ok")
