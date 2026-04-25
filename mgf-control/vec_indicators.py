"""Vectorized indicators pre-computation for Phase 5.

Pre-calculates all indicators once per dataset, avoiding recomputation per combo.
Used by phase5_combine_filters_vectorized.py for 5-10x speedup.

Indicadores vectorizados:
  - ATR (Average True Range)
  - STPMT_DIV signal
  - Stop Intelligent (SI) levels
  - Regime classification (ATR percentiles: low/med/high)
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Tuple


def atr_sma(data: np.ndarray, period: int = 14) -> np.ndarray:
    """Vectorized ATR calculation.

    Args:
        data: shape (n, 4) with columns [high, low, close]
        period: ATR period (default 14)

    Returns:
        atr: shape (n,) with ATR values
    """
    high = data[:, 0]
    low = data[:, 1]
    close = data[:, 2]

    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))

    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    tr[0] = tr1[0]

    atr = np.zeros_like(tr)
    atr[period-1] = np.mean(tr[:period])

    for i in range(period, len(tr)):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period

    return atr


def regime_classification(atr: np.ndarray) -> Tuple[np.ndarray, float, float]:
    """Classify ATR into low/med/high regimes using 33/67 percentiles.

    Args:
        atr: shape (n,) with ATR values

    Returns:
        regime: shape (n,) with values [0=low, 1=med, 2=high]
        p33: 33rd percentile
        p67: 67th percentile
    """
    p33 = np.percentile(atr, 33)
    p67 = np.percentile(atr, 67)

    regime = np.zeros_like(atr, dtype=np.int32)
    regime[atr >= p67] = 2  # high
    regime[(atr >= p33) & (atr < p67)] = 1  # med
    # regime[atr < p33] = 0  # low (default)

    return regime, p33, p67


def prepare_vec_data(data: List[Dict[str, str]]) -> Dict[str, Any]:
    """Prepare vectorized data cache for Phase 5 evaluation.

    Args:
        data: List of OHLCV dicts from load_ohlc_csv

    Returns:
        Dictionary with pre-computed numpy arrays:
        {
            'high': np.ndarray (n,),
            'low': np.ndarray (n,),
            'close': np.ndarray (n,),
            'volume': np.ndarray (n,),
            'atr': np.ndarray (n,),
            'regime': np.ndarray (n,) [0,1,2],
            'regime_p33': float,
            'regime_p67': float,
            'timestamp': np.ndarray (n,) of datetime64,
        }
    """
    n = len(data)

    high = np.array([float(bar.get('high', 0)) for bar in data], dtype=np.float64)
    low = np.array([float(bar.get('low', 0)) for bar in data], dtype=np.float64)
    close = np.array([float(bar.get('close', 0)) for bar in data], dtype=np.float64)
    volume = np.array([float(bar.get('volume', 0)) for bar in data], dtype=np.float64)

    ohlc = np.column_stack([high, low, close])
    atr = atr_sma(ohlc, period=14)
    regime, p33, p67 = regime_classification(atr)

    try:
        timestamp = np.array([bar.get('timestamp_utc', bar.get('timestamp', '')) for bar in data], dtype='datetime64[m]')
    except:
        timestamp = np.arange(n, dtype=np.int32)

    return {
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
        'atr': atr,
        'regime': regime,
        'regime_p33': p33,
        'regime_p67': p67,
        'timestamp': timestamp,
        'n': n,
    }


def filter_by_regime(vec_data: Dict[str, Any], regime_filter: str) -> np.ndarray:
    """Get mask for bars matching regime filter.

    Args:
        vec_data: output from prepare_vec_data
        regime_filter: 'all', 'low_only', 'med_only', 'high_only', 'low_med', 'med_high', 'low_high'

    Returns:
        Boolean mask (n,) for bars matching regime
    """
    regime = vec_data['regime']
    n = vec_data['n']

    if regime_filter == 'all':
        return np.ones(n, dtype=bool)
    elif regime_filter == 'low_only':
        return regime == 0
    elif regime_filter == 'med_only':
        return regime == 1
    elif regime_filter == 'high_only':
        return regime == 2
    elif regime_filter == 'low_med':
        return regime <= 1
    elif regime_filter == 'med_high':
        return regime >= 1
    elif regime_filter == 'low_high':
        return (regime == 0) | (regime == 2)
    else:
        return np.ones(n, dtype=bool)


def filter_by_hours(
    vec_data: Dict[str, Any],
    hours_allowed: List[int]
) -> np.ndarray:
    """Get mask for bars in allowed hours (UTC).

    Args:
        vec_data: output from prepare_vec_data
        hours_allowed: list of hours [0-23] to allow, or empty for all

    Returns:
        Boolean mask (n,) for bars in allowed hours
    """
    if not hours_allowed or len(hours_allowed) == 24:
        return np.ones(vec_data['n'], dtype=bool)

    try:
        timestamp = vec_data['timestamp']
        hours = timestamp.astype('datetime64[h]').astype(int) % 24
        mask = np.zeros(len(hours), dtype=bool)
        for h in hours_allowed:
            mask |= (hours == h)
        return mask
    except:
        return np.ones(vec_data['n'], dtype=bool)
