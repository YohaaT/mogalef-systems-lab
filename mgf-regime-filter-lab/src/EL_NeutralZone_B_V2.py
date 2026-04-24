from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


Number = Optional[float]


@dataclass
class NeutralZoneBV2Result:
    line: List[Number]
    ret_mid: List[Number]
    milieu: List[Number]
    band: List[Number]
    senti: List[int]
    marqueur_ret: List[Optional[int]]
    marqueur_mme: List[Optional[int]]
    haut: List[Number]
    bas: List[Number]

    def as_dict(self) -> Dict[str, List[Number]]:
        return {
            "line": self.line,
            "ret_mid": self.ret_mid,
            "milieu": self.milieu,
            "band": self.band,
            "senti": self.senti,
            "marqueurRET": self.marqueur_ret,
            "marqueurMME": self.marqueur_mme,
            "haut": self.haut,
            "bas": self.bas,
        }


class NeutralZoneBV2:
    def __init__(
        self,
        use_as: str = "filter",
        mme_period: int = 150,
        ret_window: int = 90,
        trend_indic_size: int = 15,
        vue_trend: bool = True,
        sens: str = "normal",
    ) -> None:
        if use_as not in {"filter", "signal"}:
            raise ValueError("use_as must be 'filter' or 'signal'")
        if sens not in {"normal", "inverse"}:
            raise ValueError("sens must be 'normal' or 'inverse'")
        self.use_as = use_as
        self.mme_period = max(1, mme_period)
        self.ret_window = max(1, ret_window)
        self.trend_indic_size = max(1, trend_indic_size)
        self.vue_trend = vue_trend
        self.sens = sens

    @staticmethod
    def _ema(values: List[float], period: int) -> List[Number]:
        out: List[Number] = [None] * len(values)
        alpha = 2.0 / (period + 1.0)
        prev: Number = None
        for i, value in enumerate(values):
            prev = value if prev is None else (alpha * value) + ((1.0 - alpha) * prev)
            out[i] = prev
        return out

    @staticmethod
    def _rolling_high(values: List[float], window: int) -> List[Number]:
        out: List[Number] = [None] * len(values)
        for i in range(len(values)):
            if i + 1 < window:
                continue
            out[i] = max(values[i - window + 1 : i + 1])
        return out

    @staticmethod
    def _rolling_low(values: List[float], window: int) -> List[Number]:
        out: List[Number] = [None] * len(values)
        for i in range(len(values)):
            if i + 1 < window:
                continue
            out[i] = min(values[i - window + 1 : i + 1])
        return out

    def compute(self, high: List[float], low: List[float], close: List[float], tick_size: float) -> NeutralZoneBV2Result:
        n = len(close)
        if not (len(high) == len(low) == n):
            raise ValueError("All inputs must have same length")
        if tick_size <= 0:
            raise ValueError("tick_size must be > 0")

        line = self._ema(close, self.mme_period)
        haut = self._rolling_high(high, self.ret_window)
        bas = self._rolling_low(low, self.ret_window)
        ret_mid: List[Number] = [None] * n
        milieu: List[Number] = [None] * n
        band: List[Number] = [None] * n
        marqueur_ret: List[Optional[int]] = [None] * n
        marqueur_mme: List[Optional[int]] = [None] * n
        senti: List[int] = [50] * n

        for i in range(n):
            if haut[i] is not None and bas[i] is not None:
                ret_mid[i] = (haut[i] + bas[i]) / 2.0
            if self.vue_trend and ret_mid[i] is not None and line[i] is not None:
                milieu[i] = (ret_mid[i] + line[i]) / 2.0
                band[i] = milieu[i]

        for i in range(n - 2, -1, -1):
            senti[i] = 50
            marqueur_ret[i] = marqueur_ret[i + 1]
            if ret_mid[i] is not None and ret_mid[i + 1] is not None:
                if ret_mid[i] > ret_mid[i + 1]:
                    marqueur_ret[i] = 1
                elif ret_mid[i] < ret_mid[i + 1]:
                    marqueur_ret[i] = -1

            if line[i] is not None and line[i + 1] is not None:
                marqueur_mme[i] = 1 if line[i] >= line[i + 1] else -1

            bullish = marqueur_ret[i] == 1 and marqueur_mme[i] == 1
            bearish = marqueur_ret[i] == -1 and marqueur_mme[i] == -1

            if bullish:
                if milieu[i] is not None:
                    band[i] = milieu[i] + (tick_size * self.trend_indic_size)
                senti[i] = 100 if self.sens == "normal" else 0
                if self.use_as == "signal":
                    senti[i] = 50
                    prev_bull = marqueur_ret[i + 1] == 1 and marqueur_mme[i + 1] == 1
                    if not prev_bull:
                        senti[i] = 100 if self.sens == "normal" else 0
            elif bearish:
                if milieu[i] is not None:
                    band[i] = milieu[i] - (tick_size * self.trend_indic_size)
                senti[i] = 0 if self.sens == "normal" else 100
                if self.use_as == "signal":
                    senti[i] = 50
                    prev_bear = marqueur_ret[i + 1] == -1 and marqueur_mme[i + 1] == -1
                    if not prev_bear:
                        senti[i] = 0 if self.sens == "normal" else 100

        if n >= 1:
            senti[-1] = 50

        return NeutralZoneBV2Result(
            line=line,
            ret_mid=ret_mid,
            milieu=milieu,
            band=band,
            senti=senti,
            marqueur_ret=marqueur_ret,
            marqueur_mme=marqueur_mme,
            haut=haut,
            bas=bas,
        )
