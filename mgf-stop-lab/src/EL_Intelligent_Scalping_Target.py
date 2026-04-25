"""Intelligent Scalping Target (Eric Lefort / Mogalef).

Port of EL_Intelligent_Scalping_Target.txt. The target shares the calculation
of Stop Intelligent but with INVERTED roles:

- For a LONG position: target uses recent HIGHS + Space (above current price),
  and adjusts CLOSER to entry over time when the trade goes against expectation
  (minimising the loss as MTI describes). Once the target moves down it never
  moves back up away from the price.
- For a SHORT position: target uses recent LOWS - Space (below current price),
  with the symmetric closer-only adjustment.

Implementation: reuse StopIntelligent.compute() with market_position inverted
(actual long -> pass -1, actual short -> pass 1). The resulting stop series
IS the target series.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from EL_Stop_Intelligent import StopIntelligent, StopIntelligentResult


Number = Optional[float]


@dataclass
class ScalpingTargetResult:
    target: List[Number]
    space: List[Number]
    flaglong_actual: List[int]


class IntelligentScalpingTarget:
    def __init__(
        self,
        quality: int = 2,
        recent_volat: int = 2,
        ref_volat: int = 20,
        coef_volat: float = 3.0,
        first_low_or_more: int = 2,
        first_high_or_more: int = 2,
        wait_for_xtrem: int = 0,
    ) -> None:
        self._stop = StopIntelligent(
            quality=quality,
            recent_volat=recent_volat,
            ref_volat=ref_volat,
            coef_volat=coef_volat,
            first_low_or_more=first_low_or_more,
            first_high_or_more=first_high_or_more,
            wait_for_xtrem=wait_for_xtrem,
        )

    def compute(
        self,
        high: List[float],
        low: List[float],
        close: List[float],
        market_position: List[int],
    ) -> ScalpingTargetResult:
        inverted = [-mp if mp != 0 else 0 for mp in market_position]
        res: StopIntelligentResult = self._stop.compute(high, low, close, inverted)
        return ScalpingTargetResult(
            target=res.stop,
            space=res.space,
            flaglong_actual=list(market_position),
        )
