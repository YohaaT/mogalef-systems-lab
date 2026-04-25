"""
Conversor TXT → CSV para V2 framework

Input:  {ASSET}_Continuous_{TF}.txt (formato: YYYYMMDD HHMMSS;o;h;l;c;v)
Output: {ASSET}_full_{TF}.csv (formato CSV estándar para V2)

Uso:
  python3 convert_to_csv.py
"""

import csv
from pathlib import Path
from datetime import datetime

INPUT_DIR = Path(".")
OUTPUT_DIR = Path(".")

# Mapping de nombres de archivo entrada → salida
CONVERSIONS = [
    ("ES_Continuous_5m.txt", "ES_full_5m.csv"),
    ("ES_Continuous_10m.txt", "ES_full_10m.csv"),
    ("ES_Continuous_15m.txt", "ES_full_15m.csv"),
    ("FDAX_Continuous_5m.txt", "FDAX_full_5m.csv"),
    ("FDAX_Continuous_10m.txt", "FDAX_full_10m.csv"),
    ("FDAX_Continuous_15m.txt", "FDAX_full_15m.csv"),
    ("NQ_Continuous_5m.txt", "MNQ_full_5m.csv"),
    ("NQ_Continuous_10m.txt", "MNQ_full_10m.csv"),
    ("NQ_Continuous_15m.txt", "MNQ_full_15m.csv"),
]


def convert_line(line: str) -> dict:
    """
    Convierte una línea del formato original a dict CSV.

    Input:  "20170102 230000;2243.0;2244.25;2242.75;2243.0;1972"
    Output: {"timestamp": "2017-01-02 23:00:00", "open": "2243.0", ...}
    """
    parts = line.strip().split(";")
    if len(parts) < 6:
        return None

    ts_str = parts[0]  # "20170102 230000"
    try:
        dt = datetime.strptime(ts_str, "%Y%m%d %H%M%S")
        timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

    return {
        "timestamp_utc": timestamp,
        "timestamp": timestamp,
        "open": parts[1],
        "high": parts[2],
        "low": parts[3],
        "close": parts[4],
        "volume": parts[5],
    }


def convert_file(input_file: Path, output_file: Path) -> int:
    """Convierte UN archivo TXT → CSV. Retorna número de filas convertidas."""
    if not input_file.exists():
        print(f"  [SKIP] {input_file.name} no encontrado")
        return 0

    rows_ok = 0
    rows_err = 0

    with open(input_file, "r") as fin, open(output_file, "w", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=["timestamp_utc", "timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()

        for line in fin:
            row = convert_line(line)
            if row:
                writer.writerow(row)
                rows_ok += 1
            else:
                rows_err += 1

    if rows_err > 0:
        print(f"  [WARN] {input_file.name}: {rows_err} filas con error")

    return rows_ok


def main():
    print("\n" + "="*80)
    print("CONVERSOR TXT >> CSV para V2 Framework")
    print("="*80 + "\n")

    total_rows = 0

    for input_name, output_name in CONVERSIONS:
        input_file = INPUT_DIR / input_name
        output_file = OUTPUT_DIR / output_name

        rows = convert_file(input_file, output_file)
        if rows > 0:
            total_rows += rows
            print(f"  OK {input_name:<30} >> {output_name:<25} ({rows:,} filas)")

    print(f"\n{'='*80}")
    print(f"TOTAL: {total_rows:,} filas convertidas")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
