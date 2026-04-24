from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, List, Optional, Sequence, Union


Number = Optional[float]
DateLike = Union[str, int, date, datetime]


@dataclass
class MogalefTrendFilterV2Result:
    indic1: List[Number]
    indic5: List[Number]
    indic15: List[Number]
    sens_r1: List[Optional[int]]
    sens_r5: List[Optional[int]]
    sens_r15: List[Optional[int]]
    cases: List[Optional[int]]
    sentiment: List[str]


class MogalefTrendFilterV2:
    CASE_LOOKUP = {
        (1, 1, 1): 8,
        (1, 1, -1): 7,
        (1, -1, 1): 6,
        (1, -1, -1): 5,
        (-1, 1, 1): 4,
        (-1, 1, -1): 3,
        (-1, -1, 1): 2,
        (-1, -1, -1): 1,
    }

    def __init__(
        self,
        r1: int = 1,
        r2: int = 90,
        r3: int = 150,
        trade_only_case: int = 0,
        blocked_cases: Optional[Iterable[int]] = None,
        off_on: int = 1,
        enforce_date_kill_switch: bool = True,
    ) -> None:
        self.r1 = max(1, r1)
        self.r2 = max(1, r2)
        self.r3 = max(1, r3)
        self.trade_only_case = max(0, min(8, trade_only_case))
        self.blocked_cases = {case for case in (blocked_cases or []) if 1 <= case <= 8}
        self.off_on = off_on
        self.enforce_date_kill_switch = enforce_date_kill_switch

    @staticmethod
    def _rolling_low(values: Sequence[float], window: int) -> List[Number]:
        out: List[Number] = [None] * len(values)
        for i in range(len(values)):
            if i + 1 < window:
                continue
            out[i] = min(values[i - window + 1 : i + 1])
        return out

    @staticmethod
    def _rolling_high(values: Sequence[float], window: int) -> List[Number]:
        out: List[Number] = [None] * len(values)
        for i in range(len(values)):
            if i + 1 < window:
                continue
            out[i] = max(values[i - window + 1 : i + 1])
        return out

    @staticmethod
    def _ema(values: Sequence[Number], window: int) -> List[Number]:
        out: List[Number] = [None] * len(values)
        alpha = 2.0 / (window + 1.0)
        last: Number = None
        for i, value in enumerate(values):
            if value is None:
                continue
            last = value if last is None else (alpha * value) + ((1.0 - alpha) * last)
            out[i] = last
        return out

    @staticmethod
    def _is_after_cutoff(value: DateLike) -> bool:
        if isinstance(value, datetime):
            value = value.date()
        if isinstance(value, date):
            return value > date(2030, 12, 5)
        if isinstance(value, int):
            return value > 20301205
        if isinstance(value, str):
            cleaned = value.strip().replace("/", "-").replace("_", "-")
            if len(cleaned) == 10 and cleaned[4] == "-":
                return cleaned > "2030-12-05"
            if len(cleaned) == 10 and cleaned[2] == "-":
                day, month, year = cleaned.split("-")
                return (int(year), int(month), int(day)) > (2030, 12, 5)
        raise ValueError(f"Unsupported date value: {value!r}")

    def _repulse(
        self,
        open_: Sequence[float],
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
        length: int,
    ) -> List[Number]:
        low_l = self._rolling_low(low, length)
        high_l = self._rolling_high(high, length)
        push_up_raw: List[Number] = [None] * len(close)
        push_down_raw: List[Number] = [None] * len(close)

        for i in range(len(close)):
            shifted_open_idx = i - (length - 1)
            if shifted_open_idx < 0 or low_l[i] is None or high_l[i] is None or close[i] == 0:
                continue
            shifted_open = open_[shifted_open_idx]
            push_up_raw[i] = (((3 * close[i]) - (2 * low_l[i]) - shifted_open) * 100.0) / close[i]
            push_down_raw[i] = ((shifted_open - (3 * close[i]) + (2 * high_l[i])) * 100.0) / close[i]

        smooth_up = self._ema(push_up_raw, length * 5)
        smooth_down = self._ema(push_down_raw, length * 5)
        return [
            None if smooth_up[i] is None or smooth_down[i] is None else smooth_up[i] - smooth_down[i]
            for i in range(len(close))
        ]

    def compute(
        self,
        open_: Sequence[float],
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
        dates: Optional[Sequence[DateLike]] = None,
    ) -> MogalefTrendFilterV2Result:
        n = len(close)
        if not (len(open_) == len(high) == len(low) == n):
            raise ValueError("All OHLC inputs must have the same length")
        if dates is not None and len(dates) != n:
            raise ValueError("dates must match OHLC length")

        indic1 = self._repulse(open_, high, low, close, self.r1)
        indic5 = self._repulse(open_, high, low, close, self.r2)
        indic15 = self._repulse(open_, high, low, close, self.r3)

        sens_r1: List[Optional[int]] = [None] * n
        sens_r5: List[Optional[int]] = [None] * n
        sens_r15: List[Optional[int]] = [None] * n
        cases: List[Optional[int]] = [None] * n
        sentiment: List[str] = ["block"] * n

        for i in range(1, n):
            if i < self.r3 * 5:
                continue

            if dates is not None and self.enforce_date_kill_switch and self._is_after_cutoff(dates[i]):
                cases[i] = 0
            else:
                sens_r1[i] = 1 if indic1[i] is not None and indic1[i - 1] is not None and indic1[i] > indic1[i - 1] else -1
                sens_r5[i] = 1 if indic5[i] is not None and indic5[i - 1] is not None and indic5[i] > indic5[i - 1] else -1
                sens_r15[i] = 1 if indic15[i] is not None and indic15[i - 1] is not None and indic15[i] > indic15[i - 1] else -1

                cases[i] = self.CASE_LOOKUP[(sens_r15[i], sens_r5[i], sens_r1[i])]

            if self.off_on != 1:
                sentiment[i] = "pass"
            elif self.trade_only_case != 0:
                sentiment[i] = "pass" if cases[i] == self.trade_only_case else "block"
            else:
                sentiment[i] = "block" if cases[i] in self.blocked_cases else "pass"

        return MogalefTrendFilterV2Result(
            indic1=indic1,
            indic5=indic5,
            indic15=indic15,
            sens_r1=sens_r1,
            sens_r5=sens_r5,
            sens_r15=sens_r15,
            cases=cases,
            sentiment=sentiment,
        )
