#!/bin/bash
###############################################################################
# BASH WRAPPER: Execute COMB_001_TREND optimization on BO Server
# Usage: bash run_comb001_on_bo.sh
# Duración esperada: ~4.5 horas
###############################################################################

set -e  # Detener en error
set -u  # Detener si variable no definida

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directorio actual
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}COMB_001_TREND OPTIMIZATION - BO Server Execution${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Pre-flight checks
echo -e "${YELLOW}📋 PRE-FLIGHT VERIFICATION${NC}"
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python 3 found: $PYTHON_VERSION${NC}"

# 2. Check Python dependencies
echo -n "  Checking dependencies... "
if python3 -c "import pandas, numpy, scipy" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip3 install pandas numpy scipy --quiet || {
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# 3. Check data files
echo -e "${YELLOW}📊 Checking data files...${NC}"
DATA_DIR="$BASE_DIR/data"
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${RED}❌ Data directory not found: $DATA_DIR${NC}"
    exit 1
fi

ASSETS=("YM" "MNQ" "FDAX" "ES")
for ASSET in "${ASSETS[@]}"; do
    FILE="$DATA_DIR/${ASSET}_continuous.Last.txt"
    if [ -f "$FILE" ]; then
        SIZE=$(du -h "$FILE" | cut -f1)
        echo -e "${GREEN}✓ $ASSET: $SIZE${NC}"
    else
        echo -e "${RED}❌ Missing: $FILE${NC}"
        exit 1
    fi
done

# 4. Check output directory
echo -e "${YELLOW}📁 Creating output directories...${NC}"
mkdir -p "$BASE_DIR/optimization_results/COMB_001_TREND/REPORTS"
echo -e "${GREEN}✓ Output directories ready${NC}"

# 5. Check master script
echo -e "${YELLOW}🔧 Checking master script...${NC}"
MASTER_SCRIPT="$SCRIPT_DIR/run_all_comb001_optimizations.py"
if [ ! -f "$MASTER_SCRIPT" ]; then
    echo -e "${RED}❌ Master script not found: $MASTER_SCRIPT${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Master script found${NC}"

# 6. Disk space check
echo -e "${YELLOW}💾 Checking disk space...${NC}"
AVAILABLE=$(df "$BASE_DIR" | tail -1 | awk '{print $4}')
AVAILABLE_GB=$((AVAILABLE / 1024 / 1024))
if [ "$AVAILABLE_GB" -lt 2 ]; then
    echo -e "${RED}⚠️  Warning: Only ${AVAILABLE_GB}GB available (2GB recommended)${NC}"
else
    echo -e "${GREEN}✓ ${AVAILABLE_GB}GB available${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ PRE-FLIGHT CHECKS PASSED${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Mostrar cronograma esperado
echo -e "${YELLOW}⏱️  EXPECTED SCHEDULE${NC}"
echo ""
echo "  00:00 - INICIO"
echo "  00:00-00:05 - Fase 0: Preparación datos (4 min)"
echo "  00:05-01:05 - Fase 1: Señal (60 min)"
echo "  01:05-01:10 - Pausa 5 min"
echo "  01:10-02:30 - Fase 2: Contexto (80 min)"
echo "  02:30-02:35 - Pausa 5 min"
echo "  02:35-02:51 - Fase 3: Salidas (16 min)"
echo "  02:51-02:56 - Pausa 5 min"
echo "  02:56-04:00 - Fase 4: Stops (64 min)"
echo "  04:00-04:30 - Consolidación final (30 min)"
echo "  04:30 - ✅ COMPLETADA"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}⚙️  STARTING OPTIMIZATION...${NC}"
echo ""

# Cambiar a directorio mgf-control
cd "$SCRIPT_DIR"

# Ejecutar master script
START_TIME=$(date +%s)
python3 run_all_comb001_optimizations.py

# Calcular tiempo total
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))
SECONDS=$((ELAPSED % 60))

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ OPTIMIZATION COMPLETE!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}⏱️  Elapsed time: ${HOURS}h ${MINUTES}m ${SECONDS}s${NC}"
echo ""
echo -e "${YELLOW}📦 RESULTS LOCATION${NC}"
echo "  JSON Parameters: $BASE_DIR/optimization_results/COMB_001_TREND/[ASSET]/"
echo "  Reports:        $BASE_DIR/optimization_results/COMB_001_TREND/REPORTS/"
echo "  Logs:           $SCRIPT_DIR/COMB_001_EXECUTION_LOG.txt"
echo ""
echo -e "${YELLOW}🚀 NEXT STEPS${NC}"
echo "  1. Review parameters in COMB_001_COMPARISON_MATRIX.json"
echo "  2. Check final parameters for each asset"
echo "  3. Copy C# blocks from COMB_001_NT8_PARAMETERS.txt"
echo "  4. Deploy to NinjaTrader 8"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
