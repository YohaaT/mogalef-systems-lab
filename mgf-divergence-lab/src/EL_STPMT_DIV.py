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


def _sma(values: List[Number], length: int) -> List[Number]:
    out: List[Number] = [None] * len(values)
    if length <= 0:
        return out
    for i in range(length - 1, len(values)):
        window = values[i - length + 1 : i + 1]
        if any(v is None for v in window):
            continue
        out[i] = sum(window) / length
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


def _build_stpmte(high: List[float], low: List[float], close: List[float]) -> Dict[str, List[Number]]:
    ph1 = [_highest(high, i, 5) for i in range(len(close))]
    pb1 = [_lowest(low, i, 5) for i in range(len(close))]
    ph2 = [_highest(high, i, 14) for i in range(len(close))]
    pb2 = [_lowest(low, i, 14) for i in range(len(close))]
    ph3 = [_highest(high, i, 45) for i in range(len(close))]
    pb3 = [_lowest(low, i, 45) for i in range(len(close))]
    ph4 = [_highest(high, i, 75) for i in range(len(close))]
    pb4 = [_lowest(low, i, 75) for i in range(len(close))]

    def stok(ph: List[Number], pb: List[Number]) -> List[Number]:
        out: List[Number] = [None] * len(close)
        for i in range(len(close)):
            if ph[i] is None or pb[i] is None:
                continue
            den = ph[i] - pb[i]
            out[i] = 100.0 if den == 0 else 100.0 - (((ph[i] - close[i]) / den) * 100.0)
        return out

    stok1 = stok(ph1, pb1)
    stok2 = stok(ph2, pb2)
    stok3 = stok(ph3, pb3)
    stok4 = stok(ph4, pb4)
    stod1 = _sma(stok1, 3)
    stod2 = _sma(stok2, 3)
    stod3 = _sma(stok3, 14)
    stod4 = _sma(stok4, 20)

    stpmte: List[Number] = [None] * len(close)
    for i in range(len(close)):
        vals = [stod1[i], stod2[i], stod3[i], stod4[i]]
        if any(v is None for v in vals):
            continue
        stpmte[i] = ((4.1 * stod1[i]) + (2.5 * stod2[i]) + stod3[i] + (4.0 * stod4[i])) / 11.6

    ma = _sma(stpmte, 9)
    return {
        "INDIC": stpmte,
        "MA": ma,
        "Stod1": stod1,
        "Stod2": stod2,
        "Stod3": stod3,
        "Stod4": stod4,
    }


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


def _compute_divergences_from_indicator(
    indic: List[Number],
    high: List[float],
    low: List[float],
    mode: int,
    decal_entry: int,
    smooth_h: int,
    smooth_b: int,
    distance_max_h: int,
    distance_max_l: int,
) -> Dict[str, List[Number]]:
    divh = [0.0] * len(indic)
    divb = [0.0] * len(indic)
    divhi = [0.0] * len(indic)
    divbi = [0.0] * len(indic)
    pose: List[Optional[int]] = [None] * len(indic)
    sentiment: List[Optional[int]] = [None] * len(indic)
    zb: List[List[Number]] = [[] for _ in indic]
    zh: List[List[Number]] = [[] for _ in indic]
    zbi: List[List[Number]] = [[] for _ in indic]
    zhi: List[List[Number]] = [[] for _ in indic]

    high_state = PivotState()
    low_state = PivotState()
    prev_ah: Number = None
    prev_ab: Number = None

    for i in range(len(indic)):
        high_state = _update_last_high(indic, high, i, smooth_h, high_state)
        low_state = _update_last_low(indic, low, i, smooth_b, low_state)

        temp1_prev = _highest(indic, i - 1, smooth_h + 1) if i - 1 >= 0 else None
        if (
            i >= 2
            and indic[i] is not None
            and indic[i - 1] is not None
            and temp1_prev is not None
            and ((high[i] <= high[i - 1]) or (high[i] <= high[i - 2]))
            and indic[i] < indic[i - 1]
            and indic[i - 1] == temp1_prev
            and high_state.counter < distance_max_h
        ):
            high_state.current_indicator = indic[i - 1]
            high_state.current_price = _highest(high, i, smooth_h + 2)

        temp4_prev = _lowest(indic, i - 1, smooth_b + 1) if i - 1 >= 0 else None
        if (
            i >= 2
            and indic[i] is not None
            and indic[i - 1] is not None
            and temp4_prev is not None
            and ((low[i] >= low[i - 1]) or (low[i] >= low[i - 2]))
            and indic[i] > indic[i - 1]
            and indic[i - 1] == temp4_prev
            and low_state.counter < distance_max_l
        ):
            low_state.current_indicator = indic[i - 1]
            low_state.current_price = _lowest(low, i, smooth_b + 2)

        if mode in (1, 3) and high_state.current_indicator is not None and high_state.current_indicator != prev_ah:
            if (
                high_state.last_indicator is not None
                and high_state.last_price is not None
                and high_state.current_price is not None
                and high_state.last_indicator > high_state.current_indicator
                and high_state.last_price < high_state.current_price
            ):
                divb[i] = -3.0
                zh[i] = _line_segment(high_state.current_indicator, high_state.last_indicator, high_state.counter)
        if mode in (2, 3) and high_state.current_indicator is not None and high_state.current_indicator != prev_ah:
            if (
                high_state.last_indicator is not None
                and high_state.last_price is not None
                and high_state.current_price is not None
                and high_state.last_indicator < high_state.current_indicator
                and high_state.last_price > high_state.current_price
            ):
                divbi[i] = -2.0
                zhi[i] = _line_segment(high_state.current_indicator, high_state.last_indicator, high_state.counter)

        if mode in (1, 3) and low_state.current_indicator is not None and low_state.current_indicator != prev_ab:
            if (
                low_state.last_indicator is not None
                and low_state.last_price is not None
                and low_state.current_price is not None
                and low_state.last_indicator < low_state.current_indicator
                and low_state.last_price > low_state.current_price
            ):
                divh[i] = 3.0
                zb[i] = _line_segment(low_state.current_indicator, low_state.last_indicator, low_state.counter)
        if mode in (2, 3) and low_state.current_indicator is not None and low_state.current_indicator != prev_ab:
            if (
                low_state.last_indicator is not None
                and low_state.last_price is not None
                and low_state.current_price is not None
                and low_state.last_indicator > low_state.current_indicator
                and low_state.last_price < low_state.current_price
            ):
                divhi[i] = 2.0
                zbi[i] = _line_segment(low_state.current_indicator, low_state.last_indicator, low_state.counter)

        src = i - decal_entry
        if src >= 0:
            if divh[src] > 0 or divhi[src] > 0:
                pose[i] = 1
            if divb[src] < 0 or divbi[src] < 0:
                pose[i] = -1
        if pose[i] == 1:
            sentiment[i] = 100
        elif pose[i] == -1:
            sentiment[i] = 0

        prev_ah = high_state.current_indicator
        prev_ab = low_state.current_indicator

    return {
        "DIVH": divh,
        "DIVB": divb,
        "DIVHI": divhi,
        "DIVBI": divbi,
        "pose": pose,
        "sentiment": sentiment,
        "ZB": zb,
        "ZH": zh,
        "ZBI": zbi,
        "ZHI": zhi,
    }


def compute_el_stpmt_div(
    high: List[float],
    low: List[float],
    close: List[float],
    smooth_h: int = 2,
    smooth_b: int = 2,
    mode: int = 1,
    decal_entry: int = 0,
    distance_max_h: int = 200,
    distance_max_l: int = 200,
) -> Dict[str, List[Number]]:
    built = _build_stpmte(high, low, close)
    return {
        **built,
        **_compute_divergences_from_indicator(
            indic=built["INDIC"],
            high=high,
            low=low,
            mode=mode,
            decal_entry=decal_entry,
            smooth_h=smooth_h,
            smooth_b=smooth_b,
            distance_max_h=distance_max_h,
            distance_max_l=distance_max_l,
        ),
    }
