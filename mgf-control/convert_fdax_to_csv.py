"""Convert FDAX TXT data to CSV format."""

import csv
from pathlib import Path
from datetime import datetime

# Input files
fdax_24 = Path("../FDAX 12-24.Last.txt")
fdax_25 = Path("../FDAX 12-25.Last.txt")

def parse_fdax_line(line):
    """Parse FDAX format: 20240917 001700;18878;18878;18878;18878;1"""
    parts = line.strip().split(';')
    if len(parts) < 5:
        return None

    dt = parts[0]
    date_str = dt[:8]
    time_str = dt[9:] if len(dt) > 8 else "000000"

    # Convert to ISO format
    dt_obj = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
    timestamp_utc = dt_obj.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "timestamp_utc": timestamp_utc,
        "open": float(parts[1]),
        "high": float(parts[2]),
        "low": float(parts[3]),
        "close": float(parts[4]),
    }

print("Loading FDAX 12-24...")
rows_24 = []
with open(fdax_24, "r") as f:
    for line in f:
        parsed = parse_fdax_line(line)
        if parsed:
            rows_24.append(parsed)

print(f"Loaded {len(rows_24)} rows from FDAX 12-24")

print("Loading FDAX 12-25...")
rows_25 = []
with open(fdax_25, "r") as f:
    for line in f:
        parsed = parse_fdax_line(line)
        if parsed:
            rows_25.append(parsed)

print(f"Loaded {len(rows_25)} rows from FDAX 12-25")

# Combine (keep separate for now, let user decide)
all_rows = rows_24 + rows_25
all_rows.sort(key=lambda x: x["timestamp_utc"])

print(f"\nTotal combined: {len(all_rows)} rows")
print(f"Date range: {all_rows[0]['timestamp_utc']} to {all_rows[-1]['timestamp_utc']}")

# Export full combined
output_csv = Path("FDAX_combined_full.csv")
with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["timestamp_utc", "open", "high", "low", "close"])
    writer.writeheader()
    writer.writerows(all_rows)

print(f"\n[OK] Exported: {output_csv}")

# Also export separately
output_24 = Path("FDAX_12-24.csv")
with open(output_24, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["timestamp_utc", "open", "high", "low", "close"])
    writer.writeheader()
    writer.writerows(rows_24)

print(f"[OK] Exported: {output_24}")

output_25 = Path("FDAX_12-25.csv")
with open(output_25, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["timestamp_utc", "open", "high", "low", "close"])
    writer.writeheader()
    writer.writerows(rows_25)

print(f"[OK] Exported: {output_25}")
print("\nReady for Phase A/B split!")
