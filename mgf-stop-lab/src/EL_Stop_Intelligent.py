from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


Number = Optional[float]


@dataclass
class StopIntelligentResult:
    stop: List[Number]
    tr: List[Number]
    avtr: List[Number]
    avtrref: List[Number]
    space: List[Number]
    haut: List[int]
    bas: List[int]
    h1: List[Number]
    h2: List[Number]
    h3: List[Number]
    b1: List[Number]
    b2: List[Number]
    b3: List[Number]
    h0: List[Number]
    b0: List[Number]
    hh0: List[Number]
    bb0: List[Number]
    stlong: List[Number]
    flaglong: List[int]


class StopIntelligent:
    def __init__(
        self,
        quality: int = 2,
        recent_volat: int = 2,
        ref_volat: int = 20,
        coef_volat: float = 5.0,
        first_low_or_more: int = 2,
        first_high_or_more: int = 2,
        wait_for_xtrem: int = 0,
    ) -> None:
        self.quality = max(1, min(3, quality))
        self.recent_volat = max(1, recent_volat)
        self.ref_volat = max(1, ref_volat)
        self.coef_volat = coef_volat
        self.first_low_or_more = max(1, min(3, first_low_or_more))
        self.first_high_or_more = max(1, min(3, first_high_or_more))
        self.wait_for_xtrem = max(0, min(3, wait_for_xtrem))

    @staticmethod
    def _rolling_sma(values: List[Number], window: int) -> List[Number]:
        out: List[Number] = [None] * len(values)
        for i in range(len(values)):
            if i + window > len(values):
                continue
            sample = values[i : i + window]
            if any(v is None for v in sample):
                continue
            out[i] = sum(sample) / window
        return out

    @staticmethod
    def _safe_min(values: List[Number]) -> Number:
        clean = [v for v in values if v is not None]
        return min(clean) if clean else None

    @staticmethod
    def _safe_max(values: List[Number]) -> Number:
        clean = [v for v in values if v is not None]
        return max(clean) if clean else None

    def compute(
        self,
        high: List[float],
        low: List[float],
        close: List[float],
        market_position: List[int],
    ) -> StopIntelligentResult:
        n = len(close)
        if not (len(high) == len(low) == len(market_position) == n):
            raise ValueError("All input series must have the same length")

        tr: List[Number] = [None] * n
        for i in range(0, n - 1):
            tr1 = high[i] - low[i]
            tr2 = abs(close[i + 1] - low[i])
            tr3 = abs(high[i] - close[i + 1])
            tr[i] = max(tr1, tr2, tr3)

        avtr = self._rolling_sma(tr, self.recent_volat)
        avtrref = self._rolling_sma(tr, self.ref_volat)

        space: List[Number] = [None] * n
        for i in range(n):
            if avtr[i] is None or avtrref[i] is None:
                continue
            space[i] = (((2 * avtrref[i]) - avtr[i]) * self.coef_volat) / 5.0

        haut = [0] * n
        bas = [0] * n
        h1: List[Number] = [None] * n
        h2: List[Number] = [None] * n
        h3: List[Number] = [None] * n
        b1: List[Number] = [None] * n
        b2: List[Number] = [None] * n
        b3: List[Number] = [None] * n

        for i in range(n - 1, -1, -1):
            if self.quality == 1:
                if i + 3 < n and (
                    ((high[i] < high[i + 1]) and (high[i + 1] > high[i + 2]))
                    or (
                        (high[i] < high[i + 1])
                        and (high[i + 1] >= high[i + 2])
                        and (high[i + 2] > high[i + 3])
                    )
                ):
                    haut[i] = 1
                if i + 3 < n and (
                    ((low[i] > low[i + 1]) and (low[i + 1] < low[i + 2]))
                    or (
                        (low[i] > low[i + 1])
                        and (low[i + 1] <= low[i + 2])
                        and (low[i + 2] < low[i + 3])
                    )
                ):
                    bas[i] = 1
            elif self.quality == 2:
                if i + 4 < n and (
                    (high[i] < high[i + 2])
                    and (high[i + 1] < high[i + 2])
                    and (high[i + 3] <= high[i + 2])
                    and (high[i + 2] > high[i + 4])
                ):
                    haut[i] = 2
                if i + 4 < n and (
                    (low[i] > low[i + 2])
                    and (low[i + 1] > low[i + 2])
                    and (low[i + 3] >= low[i + 2])
                    and (low[i + 4] >= low[i + 2])
                ):
                    bas[i] = 2
            else:
                if i + 6 < n and (
                    (high[i] < high[i + 3])
                    and (high[i + 1] < high[i + 3])
                    and (high[i + 2] <= high[i + 3])
                    and (high[i + 3] >= high[i + 4])
                    and (high[i + 3] >= high[i + 5])
                    and (high[i + 3] >= high[i + 6])
                ):
                    haut[i] = 3
                if i + 6 < n and (
                    (low[i] > low[i + 3])
                    and (low[i + 1] > low[i + 3])
                    and (low[i + 2] >= low[i + 3])
                    and (low[i + 3] <= low[i + 4])
                    and (low[i + 3] <= low[i + 5])
                    and (low[i + 3] <= low[i + 6])
                ):
                    bas[i] = 3

            next_i = i + 1
            if haut[i] > 0 and i + self.quality < n:
                h3[i] = h2[next_i] if next_i < n else None
                h2[i] = h1[next_i] if next_i < n else None
                h1[i] = high[i + self.quality]
            else:
                h3[i] = h3[next_i] if next_i < n else None
                h2[i] = h2[next_i] if next_i < n else None
                h1[i] = h1[next_i] if next_i < n else None

            if bas[i] > 0 and i + self.quality < n:
                b3[i] = b2[next_i] if next_i < n else None
                b2[i] = b1[next_i] if next_i < n else None
                b1[i] = low[i + self.quality]
            else:
                b3[i] = b3[next_i] if next_i < n else None
                b2[i] = b2[next_i] if next_i < n else None
                b1[i] = b1[next_i] if next_i < n else None

        stop: List[Number] = [None] * n
        h0: List[Number] = [None] * n
        b0: List[Number] = [None] * n
        hh0: List[Number] = [None] * n
        bb0: List[Number] = [None] * n
        stlong: List[Number] = [None] * n
        flaglong: List[int] = [0] * n

        last_flag = 0
        for i in range(n - 1, -1, -1):
            if market_position[i] == 1:
                last_flag = 1
            elif market_position[i] == -1:
                last_flag = -1
            flaglong[i] = last_flag

            if self.wait_for_xtrem > 0:
                bb0[i] = b1[i]
                if self.wait_for_xtrem == 2:
                    bb0[i] = self._safe_min([b1[i], b2[i]])
                elif self.wait_for_xtrem > 2:
                    bb0[i] = self._safe_min([b1[i], b2[i], b3[i]])

                hh0[i] = h1[i]
                if self.wait_for_xtrem == 2:
                    hh0[i] = self._safe_max([h1[i], h2[i]])
                elif self.wait_for_xtrem >= 3:
                    hh0[i] = self._safe_max([h1[i], h2[i], h3[i]])

            if flaglong[i] == 1:
                b0[i] = b1[i]
                if self.first_low_or_more == 2:
                    b0[i] = self._safe_min([b1[i], b2[i]])
                elif self.first_low_or_more > 2:
                    b0[i] = self._safe_min([b1[i], b2[i], b3[i]])

                if b0[i] is None or space[i] is None:
                    continue

                stlong[i] = b0[i] - space[i]
                if stlong[i] > close[i] or stlong[i] < 0.01:
                    stlong[i] = close[i] - abs(space[i])

                prev_i = i + 1
                should_hold = False
                if prev_i < n and flaglong[prev_i] == 1 and stop[prev_i] is not None and stlong[i] is not None:
                    if stlong[i] < stop[prev_i]:
                        should_hold = True
                    if self.wait_for_xtrem > 0 and hh0[prev_i] is not None and high[i] <= hh0[prev_i]:
                        should_hold = True

                stop[i] = stop[prev_i] if should_hold and prev_i < n else stlong[i]

            elif flaglong[i] == -1:
                h0[i] = h1[i]
                if self.first_high_or_more == 2:
                    h0[i] = self._safe_max([h1[i], h2[i]])
                elif self.first_high_or_more >= 3:
                    h0[i] = self._safe_max([h1[i], h2[i], h3[i]])

                if h0[i] is None or space[i] is None:
                    continue

                stlong[i] = h0[i] + space[i]
                if stlong[i] < close[i]:
                    stlong[i] = close[i] + abs(space[i])

                prev_i = i + 1
                should_hold = False
                if prev_i < n and flaglong[prev_i] == -1 and stop[prev_i] is not None and stlong[i] is not None:
                    if stlong[i] > stop[prev_i]:
                        should_hold = True
                    if self.wait_for_xtrem > 0 and bb0[prev_i] is not None and low[i] >= bb0[prev_i]:
                        should_hold = True

                stop[i] = stop[prev_i] if should_hold and prev_i < n else stlong[i]

        return StopIntelligentResult(
            stop=stop,
            tr=tr,
            avtr=avtr,
            avtrref=avtrref,
            space=space,
            haut=haut,
            bas=bas,
            h1=h1,
            h2=h2,
            h3=h3,
            b1=b1,
            b2=b2,
            b3=b3,
            h0=h0,
            b0=b0,
            hh0=hh0,
            bb0=bb0,
            stlong=stlong,
            flaglong=flaglong,
        )
