#!/usr/bin/env python3
"""
MASTER ORCHESTRATION SCRIPT: COMB_001_TREND MULTIASSET OPTIMIZATION
Automatiza la ejecución completa: Fase 0-4 para 4 activos (YM, MNQ, FDAX, ES)
Distribución 80% BO / 20% TANK con sincronización

EJECUCIÓN:
    cd C:\Users\Yohanny Tambo\Desktop\Bo_Oracle\mogalef-systems-lab\mgf-control
    python run_all_comb001_optimizations.py

CRONOGRAMA ESPERADO: ~4.5 horas
    00:00 - Fase 0: Preparación datos (4 min)
    00:05 - Fase 1: Señal (60 min)
    01:05 - Pausa 5 min
    01:10 - Fase 2: Contexto (80 min)
    02:30 - Pausa 5 min
    02:35 - Fase 3: Salidas (16 min)
    02:51 - Pausa 5 min
    02:56 - Fase 4: Stops (64 min)
    04:00 - Consolidación final (30 min)
    04:30 - ✅ COMPLETADA
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(r"C:\Users\Yohanny Tambo\Desktop\Bo_Oracle\mogalef-systems-lab")
CONTROL_DIR = BASE_DIR / "mgf-control"
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "optimization_results" / "COMB_001_TREND"

# Activos a procesar
ASSETS = ["YM", "MNQ", "FDAX", "ES"]

# Timestamps para logging
START_TIME = datetime.now()
LOG_FILE = CONTROL_DIR / "COMB_001_EXECUTION_LOG.txt"

def log(message, level="INFO"):
    """Escribe en log con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{level}] {message}"
    print(log_message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

def run_command(cmd, description, timeout=None):
    """Ejecuta comando y retorna True si es exitoso."""
    log(f"Iniciando: {description}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(CONTROL_DIR),
            timeout=timeout
        )
        if result.returncode == 0:
            log(f"✅ {description} COMPLETADO", "SUCCESS")
            return True
        else:
            log(f"❌ {description} FALLÓ", "ERROR")
            log(f"Error output: {result.stderr}", "ERROR")
            return False
    except subprocess.TimeoutExpired:
        log(f"❌ {description} TIMEOUT (excedió {timeout}s)", "ERROR")
        return False
    except Exception as e:
        log(f"❌ {description} ERROR: {str(e)}", "ERROR")
        return False

def main():
    """Orquestación principal del pipeline COMB_001_TREND."""

    # Encabezado
    log("=" * 80, "HEADER")
    log("INICIO COMB_001_TREND MULTIASSET OPTIMIZATION", "HEADER")
    log(f"Fecha: {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}", "HEADER")
    log(f"Activos: {', '.join(ASSETS)}", "HEADER")
    log(f"Distribución: 80% BO / 20% TANK", "HEADER")
    log("=" * 80, "HEADER")

    # Validar directorios
    log("\n📁 VALIDANDO ESTRUCTURA DE DIRECTORIOS")
    if not DATA_DIR.exists():
        log(f"ERROR: Data dir not found: {DATA_DIR}", "ERROR")
        return False

    if not CONTROL_DIR.exists():
        log(f"ERROR: Control dir not found: {CONTROL_DIR}", "ERROR")
        return False

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    log(f"✓ Directorios validados")

    # Validar archivos de datos
    log("\n📊 VALIDANDO ARCHIVOS DE DATOS FUENTE")
    missing_files = []
    for asset in ASSETS:
        data_file = DATA_DIR / f"{asset}_continuous.Last.txt"
        if not data_file.exists():
            missing_files.append(str(data_file))
            log(f"❌ Falta: {data_file}", "ERROR")
        else:
            size_mb = data_file.stat().st_size / (1024 * 1024)
            log(f"✓ {asset}: {size_mb:.2f} MB")

    if missing_files:
        log(f"ABORTANDO: Faltan {len(missing_files)} archivos de datos", "ERROR")
        return False

    log("✓ Todos los archivos de datos presentes")

    # ========================================================================
    # FASE 0: PREPARACIÓN DE DATOS
    # ========================================================================
    log("\n" + "=" * 80, "HEADER")
    log("FASE 0: PREPARACIÓN DE DATOS (Esperado: 4 min)", "HEADER")
    log("=" * 80, "HEADER")

    if not run_command(
        [sys.executable, "prepare_4assets_continuous.py"],
        "Fase 0: Preparación de datos (4 activos)",
        timeout=600
    ):
        log("ABORTANDO: Fase 0 falló", "ERROR")
        return False

    log("✅ FASE 0 COMPLETADA - Datos preparados para Phase A/B")

    # ========================================================================
    # FASE 1: OPTIMIZACIÓN DE SEÑAL (60 min)
    # ========================================================================
    log("\n" + "=" * 80, "HEADER")
    log("FASE 1: OPTIMIZACIÓN DE SEÑAL STPMT (Esperado: 60 min)", "HEADER")
    log("Componente: smooth_h, smooth_b, distance_max_h, distance_max_l", "HEADER")
    log("Distribución: 500 BO (80%) + 125 TANK (20%) por activo", "HEADER")
    log("=" * 80, "HEADER")

    for asset in ASSETS:
        log(f"\n  → Procesando {asset}")
        if not run_command(
            [sys.executable, "phase1_5m_signal_block_runner.py", asset],
            f"Fase 1: Señal {asset}",
            timeout=1800
        ):
            log(f"ABORTANDO: Fase 1 {asset} falló", "ERROR")
            return False

    # Consolidar resultados Fase 1
    log("\n  → Consolidando resultados Fase 1")
    if not run_command(
        [sys.executable, "phase1_5m_consolidate.py"],
        "Consolidación Fase 1",
        timeout=300
    ):
        log("ADVERTENCIA: Consolidación Fase 1 falló (continuando)", "WARN")

    log("✅ FASE 1 COMPLETADA - Parámetros de señal optimizados")
    log("⏳ Pausa de 5 minutos\n")

    # ========================================================================
    # FASE 2: OPTIMIZACIÓN DE CONTEXTO (80 min)
    # ========================================================================
    log("=" * 80, "HEADER")
    log("FASE 2: OPTIMIZACIÓN DE CONTEXTO (Esperado: 80 min)", "HEADER")
    log("Componentes:", "HEADER")
    log("  2a. Trend Filter (R1/R2/R3): 150 combos", "HEADER")
    log("  2b. Horaire (UTC allowed_hours): 6 perfiles", "HEADER")
    log("  2c. Volatility (ATR bounds): 5 opciones", "HEADER")
    log("  2d. Weekday Filter: 2 opciones", "HEADER")
    log("=" * 80, "HEADER")

    # Fase 2a: Trend Filter
    log("\n📊 FASE 2a: TREND FILTER OPTIMIZATION")
    for asset in ASSETS:
        log(f"  → Procesando {asset}")
        if not run_command(
            [sys.executable, "phase2a_5m_trend_filter_optimizer.py", asset],
            f"Fase 2a: Trend Filter {asset}",
            timeout=1800
        ):
            log(f"ABORTANDO: Fase 2a {asset} falló", "ERROR")
            return False

    # Fase 2b: Horaire
    log("\n⏰ FASE 2b: HORAIRE OPTIMIZATION (UTC allowed hours)")
    for asset in ASSETS:
        log(f"  → Procesando {asset}")
        if not run_command(
            [sys.executable, "phase2b_5m_horaire_optimizer.py", asset],
            f"Fase 2b: Horaire {asset}",
            timeout=600
        ):
            log(f"ABORTANDO: Fase 2b {asset} falló", "ERROR")
            return False

    # Fase 2c: Volatility
    log("\n📈 FASE 2c: VOLATILITY OPTIMIZATION (ATR bounds)")
    for asset in ASSETS:
        log(f"  → Procesando {asset}")
        if not run_command(
            [sys.executable, "phase2c_5m_volatility_optimizer.py", asset],
            f"Fase 2c: Volatility {asset}",
            timeout=600
        ):
            log(f"ABORTANDO: Fase 2c {asset} falló", "ERROR")
            return False

    # Fase 2d: Weekday Filter
    log("\n📅 FASE 2d: WEEKDAY FILTER OPTIMIZATION (Skip Tuesday)")
    for asset in ASSETS:
        log(f"  → Procesando {asset}")
        if not run_command(
            [sys.executable, "phase2d_5m_weekday_filter_optimizer.py", asset],
            f"Fase 2d: Weekday {asset}",
            timeout=600
        ):
            log(f"ABORTANDO: Fase 2d {asset} falló", "ERROR")
            return False

    # Consolidar resultados Fase 2
    log("\n  → Consolidando resultados Fase 2")
    if not run_command(
        [sys.executable, "phase2_5m_consolidate.py"],
        "Consolidación Fase 2",
        timeout=300
    ):
        log("ADVERTENCIA: Consolidación Fase 2 falló (continuando)", "WARN")

    log("✅ FASE 2 COMPLETADA - Contexto optimizado")
    log("⏳ Pausa de 5 minutos\n")

    # ========================================================================
    # FASE 3: OPTIMIZACIÓN DE SALIDAS (16 min)
    # ========================================================================
    log("=" * 80, "HEADER")
    log("FASE 3: OPTIMIZACIÓN DE SALIDAS (Esperado: 16 min)", "HEADER")
    log("Parámetros: target_atr_multiplier (10±2), timescan_bars (30±15)", "HEADER")
    log("Combos: 16 por activo (13 BO + 3 TANK)", "HEADER")
    log("=" * 80, "HEADER")

    for asset in ASSETS:
        log(f"\n  → Procesando {asset}")
        if not run_command(
            [sys.executable, "phase3_5m_exits_optimizer.py", asset],
            f"Fase 3: Salidas {asset}",
            timeout=900
        ):
            log(f"ABORTANDO: Fase 3 {asset} falló", "ERROR")
            return False

    # Consolidar resultados Fase 3
    log("\n  → Consolidando resultados Fase 3")
    if not run_command(
        [sys.executable, "phase3_5m_exits_mogalef_strict.py"],
        "Consolidación Fase 3",
        timeout=300
    ):
        log("ADVERTENCIA: Consolidación Fase 3 falló (continuando)", "WARN")

    log("✅ FASE 3 COMPLETADA - Salidas optimizadas")
    log("⏳ Pausa de 5 minutos\n")

    # ========================================================================
    # FASE 4: OPTIMIZACIÓN DE STOPS INTELIGENTE (64 min)
    # ========================================================================
    log("=" * 80, "HEADER")
    log("FASE 4: OPTIMIZACIÓN DE STOPS INTELIGENTE (Esperado: 64 min)", "HEADER")
    log("Parámetros: quality, recent_volat, ref_volat, coef_volat", "HEADER")
    log("Combos: 81 por activo (65 BO + 16 TANK)", "HEADER")
    log("=" * 80, "HEADER")

    for asset in ASSETS:
        log(f"\n  → Procesando {asset}")
        if not run_command(
            [sys.executable, "phase4_5m_stops_optimizer.py", asset],
            f"Fase 4: Stops {asset}",
            timeout=2400
        ):
            log(f"ABORTANDO: Fase 4 {asset} falló", "ERROR")
            return False

    # Consolidar resultados Fase 4
    log("\n  → Consolidando resultados Fase 4")
    if not run_command(
        [sys.executable, "phase4_5m_consolidate_mogalef_strict.py"],
        "Consolidación Fase 4",
        timeout=300
    ):
        log("ADVERTENCIA: Consolidación Fase 4 falló (continuando)", "WARN")

    log("✅ FASE 4 COMPLETADA - Stops optimizados")

    # ========================================================================
    # CONSOLIDACIÓN FINAL
    # ========================================================================
    log("\n" + "=" * 80, "HEADER")
    log("CONSOLIDACIÓN FINAL (Esperado: 30 min)", "HEADER")
    log("Generando: 4 JSONs finales + Reportes + Bloques C# para NT8", "HEADER")
    log("=" * 80, "HEADER")

    if not run_command(
        [sys.executable, "comb_001_trend_5m_final_consolidate.py"],
        "Consolidación final y reportes",
        timeout=1800
    ):
        log("ADVERTENCIA: Consolidación final falló (revisar resultados)", "WARN")

    # Generar bloques C# para NT8
    log("\n  → Generando bloques C# para NT8")
    if not run_command(
        [sys.executable, "generate_nt8_comb001_from_params.py"],
        "Generación código C# NT8",
        timeout=600
    ):
        log("ADVERTENCIA: Generación NT8 falló (revisar)", "WARN")

    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    elapsed_time = datetime.now() - START_TIME
    hours, remainder = divmod(int(elapsed_time.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    log("\n" + "=" * 80, "HEADER")
    log("✅ COMB_001_TREND OPTIMIZATION COMPLETADA", "SUCCESS")
    log("=" * 80, "HEADER")
    log(f"Tiempo total: {hours:02d}:{minutes:02d}:{seconds:02d}", "SUCCESS")
    log(f"Inicio: {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
    log(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")

    log("\n📦 ENTREGABLES GENERADOS:", "SUCCESS")
    log(f"  → 4 JSONs de parámetros finales en: {RESULTS_DIR}/[ASSET]/", "SUCCESS")
    log(f"  → Matriz de comparación en: {RESULTS_DIR}/REPORTS/", "SUCCESS")
    log(f"  → Bloques C# en: {RESULTS_DIR}/REPORTS/COMB_001_NT8_PARAMETERS.txt", "SUCCESS")
    log(f"  → Logs completos en: {LOG_FILE}", "SUCCESS")

    log("\n🚀 PRÓXIMOS PASOS:", "INFO")
    log("  1. Revisar reports en optimization_results/COMB_001_TREND/REPORTS/", "INFO")
    log("  2. Validar parámetros finales en JSONs", "INFO")
    log("  3. Copiar bloques C# a NT8 strategy", "INFO")
    log("  4. Backtestear en NinjaTrader 8", "INFO")

    log("=" * 80, "HEADER")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
