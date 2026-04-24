"""
COMB_002_IMPULSE — Generador de reporte final consolidado (Markdown)

Lee COMB002_FINAL_PARAMS.json (salida de consolidate_COMB002_final_winner.py)
y genera un informe markdown listo para share con el equipo:

  - Tabla resumen 4×3 (ganadores por asset/TF con robustness/trades)
  - Decisión detallada por combo (sequential vs cross + motivo)
  - Parámetros finales de cada estrategia
  - Alertas de combos degradados (no pasan filtros)
  - Recomendaciones operacionales (live deploy, tamaño de posición, etc.)

Uso:
  python3 generate_COMB002_FINAL_report.py
  python3 generate_COMB002_FINAL_report.py --final COMB002_FINAL_PARAMS.json --out REPORT.md
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
TIMEFRAMES = ["5m", "10m", "15m"]

ROBUSTNESS_THRESHOLD = 0.80
MIN_TRADES           = 30


def fmt(v, places=4, default="N/A"):
    if v is None:
        return default
    if isinstance(v, bool):
        return "✓" if v else "✗"
    if isinstance(v, float):
        return f"{v:.{places}f}"
    return str(v)


def status_icon(entry: dict) -> str:
    s = entry.get("status", "NO_PARAMS")
    if s == "OK":
        return "✅"
    if s == "DEGRADED":
        return "⚠️"
    return "❌"


def generate_summary_table(entries: dict) -> list[str]:
    lines = [
        "## Tabla resumen — ganadores por asset/timeframe",
        "",
        "| Asset | TF | Status | Winner | Rob | PF_A | PF_B | T_A | T_B | Δ vs loser |",
        "|-------|-----|--------|--------|------|------|------|-----|-----|------------|",
    ]
    for asset in ASSETS:
        for tf in TIMEFRAMES:
            e = entries.get(f"{asset}_{tf}", {})
            delta = e.get("comparison", {}).get("delta") if e.get("comparison") else None
            delta_str = f"{delta:+.4f}" if delta is not None else "N/A"
            lines.append(
                f"| {asset} | {tf} | {status_icon(e)} | "
                f"{e.get('winner_approach', 'N/A')} | "
                f"{fmt(e.get('robustness'))} | "
                f"{fmt(e.get('phase_a_pf'))} | "
                f"{fmt(e.get('phase_b_pf'))} | "
                f"{e.get('phase_a_trades', 'N/A')} | "
                f"{e.get('phase_b_trades', 'N/A')} | "
                f"{delta_str} |"
            )
    lines.append("")
    return lines


def generate_counts_section(entries: dict) -> list[str]:
    win_seq = win_crs = win_none = 0
    ok = deg = miss = 0
    pass_rob = pass_tr = 0
    for e in entries.values():
        w = e.get("winner_approach")
        if w == "sequential": win_seq += 1
        elif w == "cross":    win_crs += 1
        else:                 win_none += 1

        s = e.get("status", "NO_PARAMS")
        if   s == "OK":       ok += 1
        elif s == "DEGRADED": deg += 1
        else:                 miss += 1

        if e.get("robustness_pass"): pass_rob += 1
        if e.get("min_trades_pass"): pass_tr += 1

    total = len(entries)
    return [
        "## Conteo global",
        "",
        f"- **Total combos:** {total}",
        f"- **Approach ganador:** sequential={win_seq} · cross={win_crs} · none={win_none}",
        f"- **Status final:** ✅ OK={ok} · ⚠️ DEGRADED={deg} · ❌ MISSING={miss}",
        f"- **Pasan rob ≥ {ROBUSTNESS_THRESHOLD}:** {pass_rob}/{total}",
        f"- **Pasan trades ≥ {MIN_TRADES} (Phase A):** {pass_tr}/{total}",
        "",
    ]


def generate_decisions_detail(entries: dict) -> list[str]:
    lines = ["## Detalle de decisión por combo", ""]
    for asset in ASSETS:
        for tf in TIMEFRAMES:
            key = f"{asset}_{tf}"
            e = entries.get(key, {})
            comp = e.get("comparison", {})
            lines.append(f"### {status_icon(e)} {asset} {tf}")
            lines.append("")
            lines.append(f"- **Winner:** `{e.get('winner_approach', 'N/A')}`")
            lines.append(f"- **Motivo:** {e.get('decision_reason', 'N/A')}")
            lines.append(f"- **Sequential Rob:** {fmt(comp.get('sequential_rob'))}")
            lines.append(f"- **Cross Rob:** {fmt(comp.get('cross_rob'))}")
            lines.append(f"- **Δ (cross − seq):** {fmt(comp.get('delta'))}")
            lines.append(f"- **Final Rob:** {fmt(e.get('robustness'))} "
                         f"(PF_A={fmt(e.get('phase_a_pf'))} · PF_B={fmt(e.get('phase_b_pf'))})")
            lines.append(f"- **Trades:** A={e.get('phase_a_trades', 'N/A')} · B={e.get('phase_b_trades', 'N/A')}")
            lines.append(f"- **Filtros:** rob_pass={fmt(e.get('robustness_pass'))} · "
                         f"trades_pass={fmt(e.get('min_trades_pass'))}")
            lines.append("")
    return lines


def generate_params_section(entries: dict) -> list[str]:
    """Tabla de parámetros finales por combo (listos para deploy)."""
    lines = [
        "## Parámetros finales por combo",
        "",
        "| Asset | TF | smooth_h/b | dist_h/l | horaire | volat | scalp_coef | ts | stop_q | stop_coef |",
        "|-------|-----|------------|----------|---------|-------|------------|-----|--------|-----------|",
    ]
    for asset in ASSETS:
        for tf in TIMEFRAMES:
            e = entries.get(f"{asset}_{tf}", {})
            lines.append(
                f"| {asset} | {tf} | "
                f"{e.get('stpmt_smooth_h', '?')}/{e.get('stpmt_smooth_b', '?')} | "
                f"{e.get('stpmt_distance_max_h', '?')}/{e.get('stpmt_distance_max_l', '?')} | "
                f"{e.get('horaire_label', 'N/A')} | "
                f"{e.get('volatility_label', 'N/A')} | "
                f"{e.get('scalping_target_coef_volat', '?')} | "
                f"{e.get('timescan_bars', '?')} | "
                f"{e.get('superstop_quality', '?')} | "
                f"{e.get('superstop_coef_volat', '?')} |"
            )
    lines.append("")
    return lines


def generate_alerts_section(entries: dict) -> list[str]:
    degraded = [(k, v) for k, v in entries.items() if v.get("status") == "DEGRADED"]
    missing  = [(k, v) for k, v in entries.items() if v.get("status") == "NO_PARAMS"]

    if not degraded and not missing:
        return ["## Alertas", "", "_Ningún combo degradado o faltante — todos los 12 pasan filtros._", ""]

    lines = ["## Alertas", ""]
    if degraded:
        lines.append("### ⚠️ Combos degradados (no pasan todos los filtros)")
        lines.append("")
        for key, e in degraded:
            flags = []
            if not e.get("robustness_pass"): flags.append(f"rob={fmt(e.get('robustness'))} < {ROBUSTNESS_THRESHOLD}")
            if not e.get("min_trades_pass"): flags.append(f"trades={e.get('phase_a_trades')} < {MIN_TRADES}")
            lines.append(f"- **{key}** — {' · '.join(flags) if flags else 'unknown'} — **NO usar en live sin hold-out adicional**")
        lines.append("")
    if missing:
        lines.append("### ❌ Combos faltantes")
        lines.append("")
        for key, e in missing:
            lines.append(f"- **{key}** — {e.get('decision_reason', 'no data')}")
        lines.append("")
    return lines


def generate_recommendations(entries: dict) -> list[str]:
    ok_combos = [k for k, v in entries.items() if v.get("status") == "OK"]
    return [
        "## Recomendaciones operacionales",
        "",
        f"1. **Deploy en live:** Solo los {len(ok_combos)} combos con status ✅ OK están listos.",
        "2. **Sizing inicial:** Comenzar con tamaño reducido (25-50% del riesgo target) durante los primeros 30 días.",
        "3. **Hold-out validation:** Antes de escalar, correr los FINAL_PARAMS sobre los últimos 3 meses (datos no usados en Phase A/B).",
        "4. **Monitoreo:** Alertar si el PF live cae por debajo del 70% del PF_B esperado durante 2 semanas consecutivas.",
        "5. **Degraded combos:** Re-optimizar con más datos o abandonar; no usar en live.",
        "6. **Re-optimización periódica:** Cada 6 meses repetir Phases 1-5 con ventanas actualizadas.",
        "",
    ]


def main():
    parser = argparse.ArgumentParser(description="Genera reporte MD desde COMB002_FINAL_PARAMS.json")
    parser.add_argument("--final", type=Path, default=Path("COMB002_FINAL_PARAMS.json"),
                        help="Ruta al JSON consolidado (default: ./COMB002_FINAL_PARAMS.json)")
    parser.add_argument("--out",   type=Path, default=Path("COMB002_FINAL_REPORT.md"),
                        help="Ruta al MD de salida (default: ./COMB002_FINAL_REPORT.md)")
    args = parser.parse_args()

    if not args.final.exists():
        print(f"[ERROR] {args.final} not found. Corre antes: consolidate_COMB002_final_winner.py")
        sys.exit(1)

    with open(args.final) as fh:
        final = json.load(fh)

    entries = final.get("entries", {})
    md = [
        f"# COMB_002_IMPULSE — Informe Final Consolidado",
        "",
        f"- **Fecha consolidación:** {final.get('consolidation_date', 'N/A')}",
        f"- **Fecha reporte:**       {date.today().strftime('%Y-%m-%d')}",
        f"- **Método:**              {final.get('method', 'N/A')}",
        f"- **Thresholds:**          Rob ≥ {final.get('thresholds', {}).get('robustness_min', '?')} · "
        f"Trades ≥ {final.get('thresholds', {}).get('trades_min', '?')} · "
        f"Tie Δ = {final.get('thresholds', {}).get('tie_delta', '?')}",
        "",
        "---",
        "",
    ]
    md += generate_counts_section(entries)
    md += ["---", ""]
    md += generate_summary_table(entries)
    md += ["---", ""]
    md += generate_params_section(entries)
    md += ["---", ""]
    md += generate_decisions_detail(entries)
    md += ["---", ""]
    md += generate_alerts_section(entries)
    md += ["---", ""]
    md += generate_recommendations(entries)

    args.out.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] {args.out}")


if __name__ == "__main__":
    main()
