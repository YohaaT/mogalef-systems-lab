"""Convert all YM TXT files to combined CSV."""

import csv
from pathlib import Path
from datetime import datetime
import glob

def parse_nt8_line(line):
    """Parse NT8 format: 20230117 001700;18878;18878;18878;18878;1"""
    parts = line.strip().split(';')
    if len(parts) < 5:
        return None
    try:
        dt = parts[0]
        date_str = dt[:8]
        time_str = dt[9:] if len(dt) > 8 else "000000"
        dt_obj = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
        timestamp_utc = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "timestamp_utc": timestamp_utc,
            "open": float(parts[1]),
            "high": float(parts[2]),
            "low": float(parts[3]),
            "close": float(parts[4]),
        }
    except:
        return None

# Find all YM files
ym_files = sorted(glob.glob("../YM*.txt"))
print(f"Found {len(ym_files)} YM files")

all_rows = []
for ym_file in ym_files:
    fname = Path(ym_file).name
    print(f"Loading {fname}...", end=" ")
    with open(ym_file, "r") as f:
        rows = []
        for line in f:
            parsed = parse_nt8_line(line)
            if parsed:
                rows.append(parsed)
    print(f"{len(rows)} rows")
    all_rows.extend(rows)

# Sort by timestamp
all_rows.sort(key=lambda x: x["timestamp_utc"])

print(f"\nTotal rows: {len(all_rows)}")
print(f"Date range: {all_rows[0]['timestamp_utc']} to {all_rows[-1]['timestamp_utc']}")

# Export combined
output_csv = Path("YM_combined_full.csv")
with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["timestamp_utc", "open", "high", "low", "close"])
    writer.writeheader()
    writer.writerows(all_rows)

print(f"[OK] Exported: {output_csv}")

# Split 60/40
split_idx = int(len(all_rows) * 0.6)
phase_a = all_rows[:split_idx]
phase_b = all_rows[split_idx:]

print(f"\nPhase A: {len(phase_a)} ({len(phase_a)/len(all_rows)*100:.1f}%)")
print(f"  {phase_a[0]['timestamp_utc']} to {phase_a[-1]['timestamp_utc']}")
print(f"Phase B: {len(phase_b)} ({len(phase_b)/len(all_rows)*100:.1f}%)")
print(f"  {phase_b[0]['timestamp_utc']} to {phase_b[-1]['timestamp_utc']}")

# Export Phase A/B
with open("YM_phase_A.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["timestamp_utc","open","high","low","close"])
    writer.writeheader()
    writer.writerows(phase_a)

with open("YM_phase_B.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["timestamp_utc","open","high","low","close"])
    writer.writeheader()
    writer.writerows(phase_b)

print(f"\n[OK] YM_phase_A.csv")
print(f"[OK] YM_phase_B.csv")
