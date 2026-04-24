#!/usr/bin/env python3
"""
Multi-Timeframe Data Preparation: YM + MNQ + FDAX + ES
Generates Phase A/B splits for any timeframe (5m, 10m, 15m, etc.)

Usage:
    python3 prepare_multiframe.py 10    → generates *_10m_phase_A/B.csv
    python3 prepare_multiframe.py 15    → generates *_15m_phase_A/B.csv
    python3 prepare_multiframe.py 5     → same as original prepare_4assets

Format input: YYYYMMDD HHMMSS;open;high;low;close;volume
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

TF_MINUTES = int(sys.argv[1]) if len(sys.argv) > 1 else 10
TF_LABEL = f"{TF_MINUTES}m"
RESAMPLE_RULE = f"{TF_MINUTES}min"

ASSETS = {
    'YM':   'YM_continuous.Last.txt',
    'MNQ':  'MNQ_continuous.Last.txt',
    'FDAX': 'FDAX_continuous.Last.txt',
    'ES':   'ES_continuous.Last.txt',
}

PHASE_A_RATIO = 0.60
BASE = Path(__file__).parent


def parse_continuous_txt(filepath: str) -> pd.DataFrame:
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                parts = line.split(';')
                if len(parts) != 6:
                    continue
                dt = datetime.strptime(parts[0], '%Y%m%d %H%M%S')
                data.append({
                    'datetime': dt,
                    'timestamp_utc': dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'open':   float(parts[1]),
                    'high':   float(parts[2]),
                    'low':    float(parts[3]),
                    'close':  float(parts[4]),
                    'volume': int(parts[5]),
                })
            except (ValueError, IndexError):
                continue
    df = pd.DataFrame(data).sort_values('datetime').reset_index(drop=True)
    return df


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    agg = df.resample(RESAMPLE_RULE).agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'volume': 'sum'
    }).dropna()
    agg.reset_index(inplace=True)
    agg['timestamp_utc'] = agg['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    return agg[['timestamp_utc', 'open', 'high', 'low', 'close']]


def process_asset(asset, filename):
    print(f"\n{'='*60}")
    print(f"  {asset}  →  {TF_LABEL} bars")
    print(f"{'='*60}")

    src = BASE / filename
    if not src.exists():
        print(f"  [ERROR] Missing: {src}")
        return None

    print(f"  Parsing 1m data...")
    df1m = parse_continuous_txt(str(src))
    print(f"  Loaded {len(df1m):,} 1m bars")

    print(f"  Resampling to {TF_LABEL}...")
    df_tf = aggregate(df1m)
    print(f"  → {len(df_tf):,} {TF_LABEL} bars  "
          f"({df1m['datetime'].iloc[0].date()} – {df1m['datetime'].iloc[-1].date()})")

    split = int(len(df_tf) * PHASE_A_RATIO)
    df_a = df_tf.iloc[:split].reset_index(drop=True)
    df_b = df_tf.iloc[split:].reset_index(drop=True)
    print(f"  Phase A: {len(df_a):,} bars (train 60%)")
    print(f"  Phase B: {len(df_b):,} bars (validate 40%)")

    file_a = BASE / f"{asset}_phase_A_{TF_LABEL}.csv"
    file_b = BASE / f"{asset}_phase_B_{TF_LABEL}.csv"
    df_a.to_csv(file_a, index=False)
    df_b.to_csv(file_b, index=False)
    print(f"  Saved: {file_a.name}")
    print(f"  Saved: {file_b.name}")

    summary = {
        "asset": asset, "timeframe": TF_LABEL,
        "source_bars_1m": len(df1m),
        "bars_resampled": len(df_tf),
        "phase_a_bars": len(df_a),
        "phase_b_bars": len(df_b),
        "date_range": f"{df1m['datetime'].iloc[0].date()} – {df1m['datetime'].iloc[-1].date()}",
    }
    (BASE / f"{asset}_prep_{TF_LABEL}_summary.json").write_text(
        json.dumps(summary, indent=2))
    return summary


def main():
    print(f"\n{'='*60}")
    print(f"MULTI-TIMEFRAME DATA PREPARATION — {TF_LABEL.upper()}")
    print(f"{'='*60}")

    totals = {"bars": 0, "phase_a": 0, "phase_b": 0}
    for asset, fname in ASSETS.items():
        s = process_asset(asset, fname)
        if s:
            totals["bars"]    += s["bars_resampled"]
            totals["phase_a"] += s["phase_a_bars"]
            totals["phase_b"] += s["phase_b_bars"]

    print(f"\n{'='*60}")
    print(f"TOTAL  {totals['bars']:>8,} {TF_LABEL} bars  "
          f"| A: {totals['phase_a']:,}  | B: {totals['phase_b']:,}")
    print(f"{'='*60}")
    print(f"\n✅ Ready for {TF_LABEL} optimization pipeline")


if __name__ == "__main__":
    main()
