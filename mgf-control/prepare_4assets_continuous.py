"""
Multi-Asset Data Preparation: YM + MNQ + FDAX + ES
Convert continuous text format to Phase A/B split with 5m OHLC aggregation
Format: YYYYMMDD HHMMSS;open;high;low;close;volume
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

ASSETS = {
    'YM': 'YM_continuous.Last.txt',
    'MNQ': 'MNQ_continuous.Last.txt',
    'FDAX': 'FDAX_continuous.Last.txt',
    'ES': 'ES_continuous.Last.txt',
}

PHASE_A_RATIO = 0.60  # First 60% = training
PHASE_B_RATIO = 0.40  # Last 40% = validation

def parse_continuous_txt(filepath: str) -> pd.DataFrame:
    """Parse continuous text format: YYYYMMDD HHMMSS;open;high;low;close;volume"""
    data = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                # Split by semicolon: "20230102 230100;3868;3868;3868;3868;4"
                parts = line.split(';')
                if len(parts) != 6:
                    continue

                timestamp_str = parts[0]  # "20230102 230100"
                open_price = float(parts[1])
                high_price = float(parts[2])
                low_price = float(parts[3])
                close_price = float(parts[4])
                volume = int(parts[5])

                # Parse timestamp: YYYYMMDD HHMMSS
                dt = datetime.strptime(timestamp_str, '%Y%m%d %H%M%S')
                timestamp_utc = dt.strftime('%Y-%m-%d %H:%M:%S')

                data.append({
                    'timestamp_utc': timestamp_utc,
                    'datetime': dt,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                })
            except (ValueError, IndexError) as e:
                continue

    df = pd.DataFrame(data)
    if len(df) == 0:
        raise ValueError(f"No valid data parsed from {filepath}")

    # Sort by datetime
    df = df.sort_values('datetime').reset_index(drop=True)
    return df

def aggregate_to_5m(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate minute data to 5-minute OHLC bars"""
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)

    # Resample to 5-minute bars
    ohlc_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    df_5m = df.resample(" 5min).agg(ohlc_dict).dropna()

    # Reset index
    df_5m.reset_index(inplace=True)
    df_5m['timestamp_utc'] = df_5m['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Keep only required columns
    df_5m = df_5m[['timestamp_utc', 'open', 'high', 'low', 'close']]

    return df_5m

def split_phase_ab(df: pd.DataFrame) -> tuple:
    """Split data into Phase A (60%) and Phase B (40%)"""
    split_idx = int(len(df) * PHASE_A_RATIO)
    df_a = df.iloc[:split_idx].reset_index(drop=True)
    df_b = df.iloc[split_idx:].reset_index(drop=True)
    return df_a, df_b

def process_asset(base_path: Path, asset: str, filename: str):
    """Process single asset: parse -> aggregate -> split -> save"""

    print(f"\n{'='*70}")
    print(f"PROCESSING: {asset}")
    print(f"{'='*70}")

    input_file = base_path / filename

    if not input_file.exists():
        print(f"[ERROR] File not found: {input_file}")
        return None

    # Parse continuous text
    print(f"[1/4] Parsing continuous text...")
    df = parse_continuous_txt(str(input_file))
    print(f"      Loaded {len(df):,} minute bars")
    print(f"      Date range: {df['timestamp_utc'].iloc[0]} to {df['timestamp_utc'].iloc[-1]}")

    # Aggregate to 5m
    print(f"[2/4] Aggregating to 5-minute bars...")
    df_5m = aggregate_to_5m(df)
    print(f"      Aggregated to {len(df_5m):,} 5m bars")
    print(f"      Compression: {len(df) / len(df_5m):.2f}x")

    # Split Phase A / Phase B
    print(f"[3/4] Splitting Phase A (60%) / Phase B (40%)...")
    df_a, df_b = split_phase_ab(df_5m)
    print(f"      Phase A: {len(df_a):,} bars (training)")
    print(f"      Phase B: {len(df_b):,} bars (validation)")

    # Save CSVs
    print(f"[4/4] Saving CSV files...")

    phase_a_file = base_path / f"{asset}_phase_A_5m.csv"
    phase_b_file = base_path / f"{asset}_phase_B_5m.csv"

    df_a.to_csv(phase_a_file, index=False)
    df_b.to_csv(phase_b_file, index=False)

    print(f"      Saved: {phase_a_file.name}")
    print(f"      Saved: {phase_b_file.name}")

    # Summary
    summary = {
        "asset": asset,
        "timeframe": "5-minute",
        "source_format": "Continuous text (YYYYMMDD HHMMSS;O;H;L;C;V)",
        "input_bars": len(df),
        "output_5m_bars": len(df_5m),
        "compression_ratio": round(len(df) / len(df_5m), 2),
        "phase_a_bars": len(df_a),
        "phase_b_bars": len(df_b),
        "phase_a_range": f"{df_a['timestamp_utc'].iloc[0]} to {df_a['timestamp_utc'].iloc[-1]}",
        "phase_b_range": f"{df_b['timestamp_utc'].iloc[0]} to {df_b['timestamp_utc'].iloc[-1]}",
        "total_range": f"{df_5m['timestamp_utc'].iloc[0]} to {df_5m['timestamp_utc'].iloc[-1]}",
        "status": "SUCCESS"
    }

    summary_file = base_path / f"{asset}_preparation_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"      Summary: {summary_file.name}")

    return summary

def main():
    base_path = Path(__file__).parent

    print("\n" + "="*70)
    print("MULTI-ASSET DATA PREPARATION")
    print("YM + MNQ + FDAX + ES -> 5-Minute OHLC (Phase A/B Split)")
    print("="*70)

    results = {}

    for asset, filename in ASSETS.items():
        try:
            summary = process_asset(base_path, asset, filename)
            if summary:
                results[asset] = summary
        except Exception as e:
            print(f"[ERROR] {asset} processing failed: {e}")
            results[asset] = {"status": "FAILED", "error": str(e)}

    # Final summary report
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)

    total_bars = sum(s.get('output_5m_bars', 0) for s in results.values() if s.get('status') == 'SUCCESS')
    total_phase_a = sum(s.get('phase_a_bars', 0) for s in results.values() if s.get('status') == 'SUCCESS')
    total_phase_b = sum(s.get('phase_b_bars', 0) for s in results.values() if s.get('status') == 'SUCCESS')

    for asset, summary in results.items():
        status = summary.get('status', 'UNKNOWN')
        if status == 'SUCCESS':
            bars = summary.get('output_5m_bars', 0)
            phase_a = summary.get('phase_a_bars', 0)
            phase_b = summary.get('phase_b_bars', 0)
            print(f"{asset:6} ✓ {bars:7,} 5m bars | Phase A: {phase_a:6,} | Phase B: {phase_b:6,}")
        else:
            print(f"{asset:6} ✗ FAILED: {summary.get('error', 'Unknown error')}")

    print(f"\n{'TOTAL':6}   {total_bars:7,} 5m bars | Phase A: {total_phase_a:6,} | Phase B: {total_phase_b:6,}")

    # Master summary JSON
    master_summary = {
        "preparation_date": datetime.now().isoformat(),
        "assets_processed": list(ASSETS.keys()),
        "phase_a_ratio": PHASE_A_RATIO,
        "phase_b_ratio": PHASE_B_RATIO,
        "total_5m_bars": total_bars,
        "total_phase_a_bars": total_phase_a,
        "total_phase_b_bars": total_phase_b,
        "asset_summaries": results,
        "status": "COMPLETE" if all(s.get('status') == 'SUCCESS' for s in results.values()) else "PARTIAL_FAILURE"
    }

    master_file = base_path / "MULTI_ASSET_PREPARATION_SUMMARY.json"
    with open(master_file, 'w') as f:
        json.dump(master_summary, f, indent=2)

    print(f"\n[OK] Master summary: {master_file.name}")
    print("\n" + "="*70)
    print("DATA PREPARATION COMPLETE - Ready for Phase 1 Optimization")
    print("="*70)

if __name__ == "__main__":
    main()
