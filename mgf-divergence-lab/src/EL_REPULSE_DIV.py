from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


Number = Optional[float]


def _highest(values: List[Number], end: int, length: int) -> Number:
    start = end - length + 1
    if start < 0:
        return None
    window = values[start : end + 1]
    if any(v is None for v in window):
        return None
    return max(window)


def _lowest(values: List[Number], end: int, length: int) -> Number:
    start = end - length + 1
    if start < 0:
        return None
    window = values[start : end + 1]
    if any(v is None for v in window):
        return None
    return min(window)


def _ema(values: List[Number], length: int) -> List[Number]:
    out: List[Number] = [None] * len(values)
    if length <= 0:
        return out
    alpha = 2.0 / (length + 1.0)
    prev: Number = None
    for i, value in enumerate(values):
        if value is None:
            continue
        prev = value if prev is None else (alpha * value) + ((1.0 - alpha) * prev)
        out[i] = prev
    return out


def _line_segment(current: Number, previous: Number, distance: Number) -> List[Number]:
    if current is None or previous is None or distance is None or distance <= 1:
        return []
    slope = (previous - current) / (distance - 1)
    return [current + slope * step for step in range(int(distance))]


@dataclass
class PivotState:
    last_indicator: Number = None
    last_price: Number = None
    current_indicator: Number = None
    current_price: Number = None
    counter: int = 0


def _repulse_series(open_: List[float], high: List[float], low: List[float], close: List[float], length: int) -> List[Number]:
    lowest = [_lowest(low, i, length) for i in range(len(close))]
    highest = [_highest(high, i, length) for i in range(len(close))]

    bull: List[Number] = [None] * len(close)
    bear: List[Number] = [None] * len(close)
    for i in range(len(close)):
        src = i - (length - 1)
        if src < 0 or lowest[i] is None or highest[i] is None or close[i] == 0:
            continue
        bull[i] = (((3.0 * close[i]) - (2.0 * lowest[i]) - open_[src]) * 100.0) / close[i]
        bear[i] = ((open_[src] - (3.0 * close[i]) + (2.0 * highest[i])) * 100.0) / close[i]

    bull_ema = _ema(bull, length * 5)
    bear_ema = _ema(bear, length * 5)
    return [
        None if bull_ema[i] is None or bear_ema[i] is None else bull_ema[i] - bear_ema[i]
        for i in range(len(close))
    ]


def _update_last_high(indic: List[Number], high: List[float], idx: int, smooth: int, state: PivotState) -> PivotState:
    temp1 = _highest(indic, idx, smooth + 1)
    if temp1 is None:
        state.counter += 1
        return state
    if smooth > 1:
        pivot_idx = idx - smooth
        temp2 = _highest(indic, idx - smooth, smooth + 1) if idx - smooth >= 0 else None
        if pivot_idx >= 0 and indic[pivot_idx] is not None and indic[pivot_idx] == temp1 and indic[pivot_idx] == temp2:
            state.last_indicator = indic[pivot_idx]
            state.last_price = _highest(high, idx, (2 * smooth) + 1)
            state.counter = smooth
            return state
    else:
        pivot_idx = idx - 3
        if pivot_idx >= 0:
            t2 = _highest(indic, idx - 2, 2)
            t3 = _highest(indic, idx - 3, 2)
            tprice = _highest(high, idx, 3)
            if indic[pivot_idx] is not None and indic[pivot_idx] == t2 and indic[pivot_idx] == t3:
                state.last_indicator = indic[pivot_idx]
                state.last_price = tprice
                state.counter = 3
                return state
    state.counter += 1
    return state


def _update_last_low(indic: List[Number], low: List[float], idx: int, smooth: int, state: PivotState) -> PivotState:
    temp4 = _lowest(indic, idx, smooth + 1)
    if temp4 is None:
        state.counter += 1
        return state
    if smooth > 1:
        pivot_idx = idx - smooth
        temp5 = _lowest(indic, idx - smooth, smooth + 1) if idx - smooth >= 0 else None
        if pivot_idx >= 0 and indic[pivot_idx] is not None and indic[pivot_idx] == temp4 and indic[pivot_idx] == temp5:
            state.last_indicator = indic[pivot_idx]
            state.last_price = _lowest(low, idx, (2 * smooth) + 1)
            state.counter = smooth
            return state
    else:
        pivot_idx = idx - 3
        if pivot_idx >= 0:
            t2 = _lowest(indic, idx - 2, 2)
            t3 = _lowest(indic, idx - 3, 2)
            tprice = _lowest(low, idx, 3)
            if indic[pivot_idx] is not None and indic[pivot_idx] == t2 and indic[pivot_idx] == t3:
                state.last_indicator = indic[pivot_idx]
                state.last_price = tprice
                state.counter = 3
                return state
    state.counter += 1
    return state


def _compute_horizon_divergences(
    indic: List[Number],
    high: List[float],
    low: List[float],
    close: List[float],
    smooth_high: int,
    smooth_low: int,
    active: bool,
    bull_value: float,
    bear_value: float,
) -> Dict[str, List[Number]]:
    bull = [0.0] * len(indic)
    bear = [0.0] * len(indic)
    zb: List[List[Number]] = [[] for _ in indic]
    zh: List[List[Number]] = [[] for _ in indic]
    high_state = PivotState()
    low_state = PivotState()
    prev_ah: Number = None
    prev_ab: Number = None

    for i in range(len(indic)):
        high_state = _update_last_high(indic, high, i, smooth_high, high_state)
        low_state = _update_last_low(indic, low, i, smooth_low, low_state)

        temp1_prev = _highest(indic, i - 1, smooth_high + 1) if i - 1 >= 0 else None
        if (
            i >= 1
            and indic[i] is not None
            and indic[i - 1] is not None
            and temp1_prev is not None
            and close[i] <= close[i - 1]
            and indic[i] < indic[i - 1]
            and indic[i - 1] == temp1_prev
        ):
            high_state.current_indicator = indic[i - 1]
            high_state.current_price = _highest(high, i, smooth_high + 2)

        temp4_prev = _lowest(indic, i - 1, smooth_low + 1) if i - 1 >= 0 else None
        if (
            i >= 1
            and indic[i] is not None
            and indic[i - 1] is not None
            and temp4_prev is not None
            and close[i] >= close[i - 1]
            and indic[i] > indic[i - 1]
            and indic[i - 1] == temp4_prev
        ):
            low_state.current_indicator = indic[i - 1]
            low_state.current_price = _lowest(low, i, smooth_low + 2)

        if active and high_state.current_indicator is not None and high_state.current_indicator != prev_ah:
            if (
                high_state.last_indicator is not None
                and high_state.last_price is not None
                and high_state.current_price is not None
                and high_state.last_indicator > high_state.current_indicator
                and high_state.last_price < high_state.current_price
            ):
                bear[i] = bear_value
                zh[i] = _line_segment(high_state.current_indicator, high_state.last_indicator, high_state.counter)

        if active and low_state.current_indicator is not None and low_state.current_indicator != prev_ab:
            if (
                low_state.last_indicator is not None
                and low_state.last_price is not None
                and low_state.current_price is not None
                and low_state.last_indicator < low_state.current_indicator
                and low_state.last_price > low_state.current_price
            ):
                bull[i] = bull_value
                zb[i] = _line_segment(low_state.current_indicator, low_state.last_indicator, low_state.counter)

        prev_ah = high_state.current_indicator
        prev_ab = low_state.current_indicator

    return {"bull": bull, "bear": bear, "ZB": zb, "ZH": zh}


def compute_el_repulse_div(
    open_: List[float],
    high: List[float],
    low: List[float],
    close: List[float],
    r1: int = 1,
    r2: int = 5,
    r3: int = 15,
    smooth_high_rep1: int = 1,
    smooth_low_rep1: int = 1,
    activ_r1: bool = True,
    smooth_high_rep5: int = 3,
    smooth_low_rep5: int = 3,
    activ_r5: bool = True,
    smooth_high_rep15: int = 6,
    smooth_low_rep15: int = 6,
    activ_r15: bool = True,
    decal_entry: int = 0,
    duree_signal: int = 1,
) -> Dict[str, List[Number]]:
    indicm = _repulse_series(open_, high, low, close, r1)
    indica = _repulse_series(open_, high, low, close, r2)
    indicb = _repulse_series(open_, high, low, close, r3)

    rep1 = _compute_horizon_divergences(indicm, high, low, close, smooth_high_rep1, smooth_low_rep1, activ_r1, 0.4, -0.4)
    rep5 = _compute_horizon_divergences(indica, high, low, close, smooth_high_rep5, smooth_low_rep5, activ_r5, 0.8, -0.8)
    rep15 = _compute_horizon_divergences(indicb, high, low, close, smooth_high_rep15, smooth_low_rep15, activ_r15, 1.0, -1.0)

    pose: List[Optional[int]] = [None] * len(close)
    sentiment: List[Optional[int]] = [None] * len(close)
    for i in range(len(close)):
        chosen: Optional[int] = None
        for offset in range(duree_signal):
            j = i - (decal_entry + offset)
            if j < 0:
                continue
            if chosen is None and activ_r1 and rep1["bull"][j] > 0:
                chosen = 1
            if chosen is None and activ_r1 and rep1["bear"][j] < 0:
                chosen = -1
            if chosen is None and activ_r5 and rep5["bull"][j] > 0:
                chosen = 1
            if chosen is None and activ_r5 and rep5["bear"][j] < 0:
                chosen = -1
            if chosen is None and activ_r15 and rep15["bull"][j] > 0:
                chosen = 1
            if chosen is None and activ_r15 and rep15["bear"][j] < 0:
                chosen = -1
        pose[i] = chosen
        if chosen == 1:
            sentiment[i] = 100
        elif chosen == -1:
            sentiment[i] = 0

    return {
        "INDICM": indicm,
        "INDICA": indica,
        "INDICB": indicb,
        "DIVHM": rep1["bull"],
        "DIVBM": rep1["bear"],
        "DIVHA": rep5["bull"],
        "DIVBA": rep5["bear"],
        "DIVHB": rep15["bull"],
        "DIVBB": rep15["bear"],
        "ZBM": rep1["ZB"],
        "ZHM": rep1["ZH"],
        "ZBA": rep5["ZB"],
        "ZHA": rep5["ZH"],
        "ZBB": rep15["ZB"],
        "ZHB": rep15["ZH"],
        "Pose": pose,
        "sentiment": sentiment,
    }
