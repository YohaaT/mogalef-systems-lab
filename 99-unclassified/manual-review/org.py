#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import shutil
import argparse
import csv
import re
import unicodedata
from datetime import datetime

BASE_DIR = Path.cwd()

VIDEO_EXTS = {
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".wmv"
}

DOC_EXTS = {
    ".txt", ".pdf", ".md", ".doc", ".docx", ".rtf"
}

# ============================================================
# ESTRUCTURA Y MAPEO CANÓNICO
# ============================================================

DESTINATIONS = {
    # ---------------- mgf-bands-lab ----------------
    "el_mogalef_bands": "mgf-bands-lab/core",
    "el_mogalef_bands_2023_jm1": "mgf-bands-lab/derived",
    "el_mogalef_stop": "mgf-stop-lab/mogalef-bands-family",

    # ---------------- mgf-regime-filter-lab ----------------
    "el_neutralzone": "mgf-regime-filter-lab/neutral-zone",
    "el_neutralzone_b_v2": "mgf-regime-filter-lab/neutral-zone",
    "el_mogalef_trend_indicator": "mgf-regime-filter-lab/case-filters",
    "el_mogalef_trend_filter": "mgf-regime-filter-lab/case-filters",
    "el_mogalef_trend_filter_v2": "mgf-regime-filter-lab/case-filters",
    "el_atr_min_max_v2": "mgf-regime-filter-lab/volatility-blockers",
    "el_block_day_2019": "mgf-regime-filter-lab/calendar-blockers",
    "el_block_hours_2019_b": "mgf-regime-filter-lab/calendar-blockers",
    "el_indice_de_force_v2024": "mgf-regime-filter-lab/market-strength",
    "el_supertrend_05": "mgf-regime-filter-lab/trend-overlays",

    # ---------------- mgf-divergence-lab ----------------
    "el_stpmt_div": "mgf-divergence-lab/stpmt",
    "el_stoch_div": "mgf-divergence-lab/stochastic",
    "el_repulse_div": "mgf-divergence-lab/repulse",
    "el_macd_div": "mgf-divergence-lab/macd",
    "el_cci_div": "mgf-divergence-lab/cci",

    # ---------------- mgf-breakout-lab ----------------
    "el_triangle_long": "mgf-breakout-lab/geometric/triangles",
    "el_triangle_short": "mgf-breakout-lab/geometric/triangles",
    "el_triangle_stop_long": "mgf-stop-lab/triangle-family",
    "el_triangle_stop_short": "mgf-stop-lab/triangle-family",
    "el_wedge_rising": "mgf-breakout-lab/geometric/wedges",
    "el_wedge_falling": "mgf-breakout-lab/geometric/wedges",
    "el_bullish_breakout2": "mgf-breakout-lab/structural-breakouts",
    "el_bearish_breakout": "mgf-breakout-lab/structural-breakouts",
    "e_xlb_indicator": "mgf-breakout-lab/line-break/indicator",
    "e_xlb_signal": "mgf-breakout-lab/line-break/signal",
    "e_xlb_signal_directional": "mgf-breakout-lab/line-break/signal_directional",
    "e_xlb_filter": "mgf-breakout-lab/line-break/filter",
    "el_autoadaptbreakout": "mgf-breakout-lab/research-tools",

    # ---------------- mgf-stop-lab ----------------
    "super_stop_long": "mgf-stop-lab/super-stop",
    "super_stop_short": "mgf-stop-lab/super-stop",
    "super_stop_long_5beta": "mgf-stop-lab/super-stop",
    "super_stop_short_5beta": "mgf-stop-lab/super-stop",
    "el_stop_keltner": "mgf-stop-lab/keltner",
    "el_stop_intelligent": "mgf-stop-lab/intelligent-family/core",
    "el_stop_intel_v2_live": "mgf-stop-lab/intelligent-family/live",
    "el_stop_intelligent_target": "mgf-stop-lab/intelligent-family/targets",
    "el_intelligent_scalping_target": "mgf-stop-lab/intelligent-family/targets",

    # ---------------- mgf-risk-lab ----------------
    "mogalef_money_management": "mgf-risk-lab/money-management",

    # ---------------- contexto / documentación ----------------
    "ce_que_jaurais_voulu_savoir_avant_mon_debut_en_trading": "mgf-control/research-context",
}

SCRIPT_NAME = "organize_mogalef_files.py"


def normalize_name(path: Path) -> str:
    """
    Normaliza el nombre del archivo para mapearlo:
    - quita extensión
    - elimina acentos
    - elimina sufijos tipo (1), (2)
    - pasa a minúsculas
    - reemplaza separadores por _
    """
    stem = path.stem.strip()

    # quitar sufijos tipo: " (1)", " (2)"
    stem = re.sub(r"\s*\(\d+\)\s*$", "", stem)

    # quitar acentos
    stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")

    # minúsculas y normalización
    stem = stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "_", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")

    return stem


def fallback_destination(file_path: Path) -> str:
    ext = file_path.suffix.lower()

    if ext in VIDEO_EXTS:
        return "99_unclassified/videos"

    if ext in DOC_EXTS:
        return "99_unclassified/manual_review/docs"

    return "99_unclassified/manual_review/other"


def ensure_unique_destination(dest_file: Path) -> Path:
    """
    Si ya existe un archivo con ese nombre, añade sufijo __dupN
    para no sobrescribir nada.
    """
    if not dest_file.exists():
        return dest_file

    counter = 1
    while True:
        candidate = dest_file.with_name(
            f"{dest_file.stem}__dup{counter}{dest_file.suffix}"
        )
        if not candidate.exists():
            return candidate
        counter += 1


def collect_files(base_dir: Path):
    """
    Solo toma archivos del nivel actual.
    No entra en subcarpetas.
    """
    files = []
    for item in base_dir.iterdir():
        if item.is_file() and item.name != SCRIPT_NAME:
            files.append(item)
    return sorted(files, key=lambda p: p.name.lower())


def organize_files(apply_changes: bool, copy_mode: bool):
    files = collect_files(BASE_DIR)
    if not files:
        print("No encontré archivos sueltos en esta carpeta.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = BASE_DIR / f"organization_log_{timestamp}.csv"

    summary = {
        "recognized": 0,
        "fallback": 0,
        "moved_or_copied": 0,
        "skipped": 0,
        "errors": 0,
    }

    rows = []

    for src in files:
        norm = normalize_name(src)
        rel_dest = DESTINATIONS.get(norm)

        if rel_dest:
            summary["recognized"] += 1
            reason = "recognized"
        else:
            rel_dest = fallback_destination(src)
            summary["fallback"] += 1
            reason = "fallback"

        dest_dir = BASE_DIR / rel_dest
        dest_file = ensure_unique_destination(dest_dir / src.name)

        rows.append({
            "source": str(src),
            "normalized_name": norm,
            "destination": str(dest_file),
            "reason": reason,
            "action": "copy" if copy_mode else "move",
            "status": "planned" if not apply_changes else "pending",
        })

        if not apply_changes:
            continue

        try:
            dest_dir.mkdir(parents=True, exist_ok=True)

            if copy_mode:
                shutil.copy2(src, dest_file)
            else:
                shutil.move(str(src), str(dest_file))

            rows[-1]["status"] = "done"
            summary["moved_or_copied"] += 1

        except Exception as e:
            rows[-1]["status"] = f"error: {e}"
            summary["errors"] += 1

    # guardar log
    with log_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["source", "normalized_name", "destination", "reason", "action", "status"]
        )
        writer.writeheader()
        writer.writerows(rows)

    # imprimir resumen
    print("=" * 72)
    print("RESUMEN")
    print("=" * 72)
    print(f"Carpeta base:           {BASE_DIR}")
    print(f"Archivos detectados:    {len(files)}")
    print(f"Reconocidos:            {summary['recognized']}")
    print(f"No reconocidos:         {summary['fallback']}")
    print(f"Ejecutado:              {'SI' if apply_changes else 'NO (dry-run)'}")
    print(f"Modo:                   {'COPY' if copy_mode else 'MOVE'}")
    print(f"Hechos:                 {summary['moved_or_copied']}")
    print(f"Errores:                {summary['errors']}")
    print(f"Log CSV:                {log_file.name}")
    print("=" * 72)

    # mostrar preview
    print("\nPREVIEW:")
    for row in rows[:30]:
        print(f"[{row['reason']}] {Path(row['source']).name}  ->  {Path(row['destination'])}")

    if len(rows) > 30:
        print(f"... y {len(rows) - 30} más")


def main():
    parser = argparse.ArgumentParser(
        description="Organiza archivos Mogalef en carpetas según la taxonomía definida."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica cambios reales. Sin esto, solo hace dry-run."
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copia en vez de mover. Si no lo usas, con --apply moverá."
    )
    args = parser.parse_args()

    organize_files(apply_changes=args.apply, copy_mode=args.copy)


if __name__ == "__main__":
    main()