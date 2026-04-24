from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict, List, Optional


Number = float


def _round_half_away_from_zero(value: float) -> int:
    if value >= 0:
        return int(value + 0.5)
    return int(value - 0.5)


@dataclass
class MogalefBandsResult:
    mog_reg_lin: List[Optional[Number]]
    mog_h: List[Optional[Number]]
    mog_b: List[Optional[Number]]
    mog_m: List[Optional[Number]]
    mog_ma: List[Optional[Number]]
    mog_stop_l: List[Optional[Number]]
    mog_stop_s: List[Optional[Number]]
    mh: List[Optional[Number]]
    mb: List[Optional[Number]]
    mm: List[Optional[Number]]
    etyp: List[Optional[Number]]
    x: List[int]
    y: List[int]

    def as_dict(self) -> Dict[str, List[Optional[Number]]]:
        return {
            "MogRegLin": self.mog_reg_lin,
            "MogH": self.mog_h,
            "MogB": self.mog_b,
            "MogM": self.mog_m,
            "MogMA": self.mog_ma,
            "MogStopL": self.mog_stop_l,
            "MogStopS": self.mog_stop_s,
            "mh": self.mh,
            "mb": self.mb,
            "mm": self.mm,
            "etyp": self.etyp,
            "X": self.x,
            "Y": self.y,
        }


class MogalefBands:
    """Rebuild conservador de EL_MOGALEF_Bands.

    Decisiones de traducción principales:
    - Se usa indexing cronológico normal, barra 0 -> barra más antigua.
    - La pasada retrospectiva del fuente se replica recorriendo de derecha a izquierda.
    - Las primeras barras sin ventana suficiente conservan `close` como `MogRegLin`, igual que el fuente.
    - La desviación estándar usa divisor poblacional (`n`), no muestral.
    - En la última barra de la pasada retrospectiva, `j+1` del host se interpreta como una celda serie
      todavía no inicializada. En Python eso se replica dejando el primer canal de la pasada nacer sin
      herencia ni stops previos, pero sí calculando `MogH/MogB/MogM` si `etyp` ya existe.
    """

    def __init__(self, n: int = 10, et_window: int = 15, coef: float = 7.0, visualisation: int = 0):
        if n < 2:
            raise ValueError("n must be >= 2")
        if et_window < 1:
            raise ValueError("et_window must be >= 1")
        self.n = n
        self.et_window = et_window
        self.coef = coef
        self.visualisation = visualisation

    @staticmethod
    def weighted_price_ticks(o: Number, h: Number, l: Number, c: Number, tick_size: Number) -> int:
        if tick_size <= 0:
            raise ValueError("tick_size must be > 0")
        weighted_price = (h + l + o + c + c) / 5.0
        return _round_half_away_from_zero(weighted_price / tick_size)

    def _compute_y(self, open_: List[Number], high: List[Number], low: List[Number], close: List[Number], tick_size: Number) -> List[int]:
        return [
            self.weighted_price_ticks(open_[i], high[i], low[i], close[i], tick_size)
            for i in range(len(close))
        ]

    def compute_regression_series(
        self,
        open_: List[Number],
        high: List[Number],
        low: List[Number],
        close: List[Number],
        tick_size: Number,
    ) -> Dict[str, List[Optional[Number]]]:
        n_bars = len(close)
        x = list(range(n_bars))
        y = self._compute_y(open_, high, low, close, tick_size)
        mog_reg_lin: List[Optional[Number]] = [None] * n_bars

        sum_x = 0.0
        sum_y = 0.0
        ssum_xy = 0.0
        sum_x2: Optional[float] = None

        for i in range(n_bars):
            if i <= self.n - 1:
                sum_x += x[i]
                sum_y += y[i]
                mog_reg_lin[i] = close[i]

                if i == self.n - 1:
                    sum_x2 = self.n * ((self.n ** 2) - 1) / 12.0
                    ssum_xy = 0.0
                    for j in range(self.n):
                        idx = i - j
                        ssum_xy += (self.n * x[idx] - sum_x) * (self.n * y[idx] - sum_y)

                    sum_xy = ssum_xy / (self.n ** 2)
                    avg_x = sum_x / self.n
                    avg_y = sum_y / self.n
                    b = sum_xy / sum_x2
                    a = avg_y - b * avg_x
                    mog_reg_lin[i] = (a + b * x[i]) * tick_size
            else:
                old_idx = i - self.n
                sum_x = sum_x + x[i] - x[old_idx]
                sum_y = sum_y + y[i] - y[old_idx]
                ssum_xy = (
                    ssum_xy
                    + (self.n * x[i] - sum_x) * (self.n * y[i] - sum_y)
                    - (self.n * x[old_idx] - sum_x) * (self.n * y[old_idx] - sum_y)
                    + self.n * (x[i] - x[old_idx]) * (y[i] - y[old_idx])
                )
                if sum_x2 is None:
                    raise RuntimeError("sum_x2 should be initialized before incremental update")
                sum_xy = ssum_xy / (self.n ** 2)
                avg_x = sum_x / self.n
                avg_y = sum_y / self.n
                b = sum_xy / sum_x2
                a = avg_y - b * avg_x
                mog_reg_lin[i] = (a + b * x[i]) * tick_size

        return {"MogRegLin": mog_reg_lin, "X": x, "Y": y}

    def rolling_std(self, series: List[Optional[Number]], window: int) -> List[Optional[Number]]:
        out: List[Optional[Number]] = [None] * len(series)
        for i in range(len(series)):
            if i + 1 < window:
                continue
            sample = series[i - window + 1 : i + 1]
            if any(v is None for v in sample):
                continue
            vals = [float(v) for v in sample if v is not None]
            mean = sum(vals) / window
            var = sum((v - mean) ** 2 for v in vals) / window
            out[i] = sqrt(var)
        return out

    def compute(
        self,
        open_: List[Number],
        high: List[Number],
        low: List[Number],
        close: List[Number],
        tick_size: Number,
    ) -> MogalefBandsResult:
        if not (len(open_) == len(high) == len(low) == len(close)):
            raise ValueError("All OHLC series must have same length")

        regression = self.compute_regression_series(open_, high, low, close, tick_size)
        mog_reg_lin = regression["MogRegLin"]
        x = regression["X"]
        y = regression["Y"]
        etyp = self.rolling_std(mog_reg_lin, self.et_window)

        n_bars = len(close)
        mog_h: List[Optional[Number]] = [None] * n_bars
        mog_b: List[Optional[Number]] = [None] * n_bars
        mog_m: List[Optional[Number]] = [None] * n_bars
        mog_ma: List[Optional[Number]] = [None] * n_bars
        mog_stop_l: List[Optional[Number]] = [None] * n_bars
        mog_stop_s: List[Optional[Number]] = [None] * n_bars
        mh: List[Optional[Number]] = [None] * n_bars
        mb: List[Optional[Number]] = [None] * n_bars
        mm: List[Optional[Number]] = [None] * n_bars

        for j in range(n_bars - 1, -1, -1):
            next_j = j + 1
            has_next = next_j < n_bars

            can_hold_channel = (
                has_next
                and mog_h[next_j] is not None
                and mog_b[next_j] is not None
                and mog_reg_lin[j] is not None
                and mog_reg_lin[j] < mog_h[next_j]
                and mog_reg_lin[j] > mog_b[next_j]
            )

            if can_hold_channel:
                mog_h[j] = mog_h[next_j]
                mog_b[j] = mog_b[next_j]
                mog_m[j] = mog_m[next_j]
                mog_ma[j] = mog_ma[next_j]
                mog_stop_s[j] = mog_stop_s[next_j]
                mog_stop_l[j] = mog_stop_l[next_j]
            else:
                if mog_reg_lin[j] is None or etyp[j] is None:
                    if self.visualisation == 0:
                        mh[j] = mog_h[j]
                        mb[j] = mog_b[j]
                        mm[j] = mog_m[j]
                    continue

                mog_h[j] = mog_reg_lin[j] + (etyp[j] * self.coef)
                mog_b[j] = mog_reg_lin[j] - (etyp[j] * self.coef)
                mog_m[j] = mog_reg_lin[j]
                mog_ma[j] = mog_m[next_j] if has_next else None

                if not has_next:
                    if self.visualisation == 0:
                        mh[j] = mog_h[j]
                        mb[j] = mog_b[j]
                        mm[j] = mog_m[j]
                    continue

                if mog_ma[j] is not None and mog_ma[j] < mog_m[j]:
                    if mog_ma[j] < mog_h[j] and mog_ma[j] > mog_b[j]:
                        mog_stop_l[j] = mog_stop_l[next_j] if has_next else None
                        mog_stop_s[j] = mog_stop_s[next_j] if has_next else None
                    else:
                        mog_stop_l[j] = mog_ma[j]
                        mog_stop_s[j] = mog_stop_s[next_j] if has_next else None

                if mog_ma[j] is not None and mog_ma[j] > mog_m[j]:
                    if mog_ma[j] < mog_h[j] and mog_ma[j] > mog_b[j]:
                        mog_stop_s[j] = mog_stop_s[next_j] if has_next else None
                        mog_stop_l[j] = mog_stop_l[next_j] if has_next else None
                    else:
                        mog_stop_s[j] = mog_ma[j]
                        mog_stop_l[j] = mog_stop_l[next_j] if has_next else None

            if self.visualisation == 0:
                mh[j] = mog_h[j]
                mb[j] = mog_b[j]
                mm[j] = mog_m[j]

        return MogalefBandsResult(
            mog_reg_lin=mog_reg_lin,
            mog_h=mog_h,
            mog_b=mog_b,
            mog_m=mog_m,
            mog_ma=mog_ma,
            mog_stop_l=mog_stop_l,
            mog_stop_s=mog_stop_s,
            mh=mh,
            mb=mb,
            mm=mm,
            etyp=etyp,
            x=x,
            y=y,
        )
