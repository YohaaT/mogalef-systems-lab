"""Prepare Phase A/B data split for walk-forward validation."""

import csv
from pathlib import Path

# Load full data
input_csv = Path("C:/Users/Yohanny Tambo/Desktop/Bo_Oracle/mogalef-systems-lab/mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv")
print(f"Loading data from: {input_csv}")

with open(input_csv, "r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

total = len(rows)
print(f"Total rows: {total}")

# Split 60/40
split_idx = int(total * 0.6)
phase_a_rows = rows[:split_idx]
phase_b_rows = rows[split_idx:]

print(f"\nSplit Point: Row {split_idx}")
print(f"Phase A: {len(phase_a_rows)} rows ({len(phase_a_rows)/total*100:.1f}%)")
print(f"Phase B: {len(phase_b_rows)} rows ({len(phase_b_rows)/total*100:.1f}%)")

# Timestamps
print(f"\nPhase A: {phase_a_rows[0]['timestamp_utc']} to {phase_a_rows[-1]['timestamp_utc']}")
print(f"Phase B: {phase_b_rows[0]['timestamp_utc']} to {phase_b_rows[-1]['timestamp_utc']}")

# Export Phase A
phase_a_csv = Path("phase_A_training.csv")
with open(phase_a_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=phase_a_rows[0].keys())
    writer.writeheader()
    writer.writerows(phase_a_rows)
print(f"\n[OK] Exported Phase A: {phase_a_csv}")

# Export Phase B
phase_b_csv = Path("phase_B_validation.csv")
with open(phase_b_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=phase_b_rows[0].keys())
    writer.writeheader()
    writer.writerows(phase_b_rows)
print(f"[OK] Exported Phase B: {phase_b_csv}")

# Export split info
with open("phase_split_info.txt", "w") as f:
    f.write("PHASE A/B SPLIT INFORMATION\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Total data rows: {total}\n")
    f.write(f"Split point: Row {split_idx}\n")
    f.write(f"Phase A (training): {len(phase_a_rows)} rows ({len(phase_a_rows)/total*100:.1f}%)\n")
    f.write(f"Phase B (validation): {len(phase_b_rows)} rows ({len(phase_b_rows)/total*100:.1f}%)\n\n")
    f.write(f"Phase A timestamp range:\n")
    f.write(f"  Start: {phase_a_rows[0]['timestamp_utc']}\n")
    f.write(f"  End:   {phase_a_rows[-1]['timestamp_utc']}\n\n")
    f.write(f"Phase B timestamp range:\n")
    f.write(f"  Start: {phase_b_rows[0]['timestamp_utc']}\n")
    f.write(f"  End:   {phase_b_rows[-1]['timestamp_utc']}\n")

print(f"[OK] Exported split info: phase_split_info.txt")
