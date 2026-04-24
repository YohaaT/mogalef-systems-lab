"""Convert FDAX tick/1m data to clean 5m OHLC bars"""

import pandas as pd
import json
from pathlib import Path

def aggregate_to_5m(input_csv: str, output_csv: str, asset: str = "FDAX"):
    """Aggregate OHLC data to 5-minute bars with proper timestamp formatting"""

    print(f"\n[{asset}] Loading {input_csv}...")
    df = pd.read_csv(input_csv)

    # Parse timestamp
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
    df.set_index('timestamp_utc', inplace=True)

    print(f"[{asset}] Input bars: {len(df)}")
    print(f"[{asset}] Date range: {df.index[0]} to {df.index[-1]}")

    # Resample to 5-minute bars
    ohlc_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }
    df_5m = df.resample('5T').agg(ohlc_dict).dropna()

    # Reset index and format timestamp
    df_5m.reset_index(inplace=True)
    df_5m['timestamp_utc'] = df_5m['timestamp_utc'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Reorder columns
    df_5m = df_5m[['timestamp_utc', 'open', 'high', 'low', 'close']]

    # Save to CSV
    df_5m.to_csv(output_csv, index=False)

    print(f"[{asset}] Output bars (5m): {len(df_5m)}")
    print(f"[{asset}] Compression ratio: {len(df)/len(df_5m):.2f}x")
    print(f"[{asset}] -> Saved to: {output_csv}")

    return df_5m

def main():
    base_path = Path(__file__).parent

    print("\n" + "="*70)
    print("FDAX DATA CONVERSION - Variable Interval -> 5-Minute OHLC")
    print("="*70)

    # Convert Phase A
    fdax_a_input = base_path / "FDAX_phase_A.csv"
    fdax_a_output = base_path / "FDAX_phase_A_5m.csv"
    df_a = aggregate_to_5m(str(fdax_a_input), str(fdax_a_output), asset="FDAX Phase A")

    # Convert Phase B
    fdax_b_input = base_path / "FDAX_phase_B.csv"
    fdax_b_output = base_path / "FDAX_phase_B_5m.csv"
    df_b = aggregate_to_5m(str(fdax_b_input), str(fdax_b_output), asset="FDAX Phase B")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Phase A: {len(df_a):,} 5m bars")
    print(f"Phase B: {len(df_b):,} 5m bars")
    print(f"Total:   {len(df_a) + len(df_b):,} 5m bars")

    # Save summary
    summary = {
        "asset": "FDAX",
        "timeframe": "5-minute",
        "phase_a_bars": len(df_a),
        "phase_b_bars": len(df_b),
        "total_bars": len(df_a) + len(df_b),
        "phase_a_range": f"{df_a['timestamp_utc'].iloc[0]} to {df_a['timestamp_utc'].iloc[-1]}",
        "phase_b_range": f"{df_b['timestamp_utc'].iloc[0]} to {df_b['timestamp_utc'].iloc[-1]}",
        "conversion_status": "SUCCESS"
    }

    summary_file = base_path / "FDAX_conversion_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n[OK] Summary saved to: {summary_file}")

    print("\n" + "="*70)
    print("CONVERSION COMPLETE - Ready for Phase 1 optimization")
    print("="*70)

if __name__ == "__main__":
    main()
