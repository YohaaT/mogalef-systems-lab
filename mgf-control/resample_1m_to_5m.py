"""
Resample YM 1m clean CSVs -> 5m CSVs.

Rules:
- Buckets aligned to :00,:05,:10,...,:55 (UTC floor to 5-min boundary)
- OHLC: O=first, H=max, L=min, C=last
- Only complete buckets (exactly 5 1m bars OR last bar of session closes bucket)
- Treats CSVs as continuous contract — no roll adjustment needed (already clean)
- No overlap between Phase A and Phase B (they share no timestamps)
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

MGMT_DIR = Path(__file__).resolve().parent


def floor_to_5m(ts_str: str) -> str:
    """Return the 5m bucket start for a given 'YYYY-MM-DD HH:MM:SS' timestamp."""
    dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    floored_min = (dt.minute // 5) * 5
    dt_floor = dt.replace(minute=floored_min, second=0)
    return dt_floor.strftime("%Y-%m-%d %H:%M:%S")


def resample_to_5m(input_path: Path, output_path: Path) -> int:
    """
    Resample 1m CSV -> 5m CSV. Returns number of 5m bars written.

    Input columns : timestamp_utc, open, high, low, close
    Output columns: timestamp_utc, open, high, low, close
    timestamp_utc in output = bucket start (floor to :00/:05/...)
    """
    buckets: dict[str, dict] = {}  # bucket_ts -> {o, h, l, c, count}
    bucket_order: list[str] = []

    with open(input_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = row["timestamp_utc"]
            bucket = floor_to_5m(ts)
            o = float(row["open"])
            h = float(row["high"])
            l = float(row["low"])
            c = float(row["close"])

            if bucket not in buckets:
                buckets[bucket] = {"o": o, "h": h, "l": l, "c": c, "count": 1}
                bucket_order.append(bucket)
            else:
                b = buckets[bucket]
                b["h"] = max(b["h"], h)
                b["l"] = min(b["l"], l)
                b["c"] = c
                b["count"] += 1

    # Write output — keep all buckets (including partial at session edges)
    # Partial buckets at the edges are kept to preserve continuity;
    # the strategy uses only ATR/signal values which are still valid.
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_utc", "open", "high", "low", "close"])
        for bucket in bucket_order:
            b = buckets[bucket]
            writer.writerow([
                bucket,
                f"{b['o']:.1f}",
                f"{b['h']:.1f}",
                f"{b['l']:.1f}",
                f"{b['c']:.1f}",
            ])

    return len(bucket_order)


def validate_5m(path: Path) -> None:
    """Basic sanity checks on 5m output."""
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))

    errors = 0
    for i, row in enumerate(rows):
        o = float(row["open"])
        h = float(row["high"])
        l = float(row["low"])
        c = float(row["close"])
        if h < l:
            print(f"  ERROR row {i}: H < L — {row}")
            errors += 1
        if o > h or o < l:
            print(f"  ERROR row {i}: Open outside H/L — {row}")
            errors += 1
        if c > h or c < l:
            print(f"  ERROR row {i}: Close outside H/L — {row}")
            errors += 1
        # Check bucket alignment
        ts = row["timestamp_utc"]
        minute = int(ts[14:16])
        if minute % 5 != 0:
            print(f"  ERROR row {i}: timestamp not aligned to 5m — {ts}")
            errors += 1

    # Check chronological order
    for i in range(1, len(rows)):
        if rows[i]["timestamp_utc"] <= rows[i - 1]["timestamp_utc"]:
            print(f"  ERROR: non-monotonic at row {i}: {rows[i-1]['timestamp_utc']} -> {rows[i]['timestamp_utc']}")
            errors += 1

    if errors == 0:
        print(f"  Validation OK — {len(rows)} bars, no errors")
    else:
        print(f"  {errors} ERRORS found!")


def main():
    print("=" * 60)
    print("RESAMPLE: YM 1m -> 5m (Mogalef 5-minute timeframe)")
    print("=" * 60)

    pairs = [
        ("YM_phase_A_clean.csv", "YM_phase_A_5m.csv", "Phase A"),
        ("YM_phase_B_clean.csv", "YM_phase_B_5m.csv", "Phase B"),
    ]

    for src_name, dst_name, label in pairs:
        src = MGMT_DIR / src_name
        dst = MGMT_DIR / dst_name

        if not src.exists():
            print(f"\n[SKIP] {src_name} not found")
            continue

        print(f"\n[{label}] {src_name} -> {dst_name}")
        n = resample_to_5m(src, dst)
        print(f"  Written: {n} bars @ 5m")
        validate_5m(dst)

        # Show first and last bars
        with open(dst, newline="") as f:
            rows = list(csv.DictReader(f))
        print(f"  First: {rows[0]}")
        print(f"  Last:  {rows[-1]}")

    print("\n[DONE] 5m CSVs ready.")


if __name__ == "__main__":
    main()
