#!/bin/bash
# Script para configurar y usar el entorno virtual del proyecto

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directorio del proyecto
PROJECT_DIR="/Users/juandiegogutierrezcortez/tramites-ai-brasil-peru"
VENV_DIR="$PROJECT_DIR/.venv"

function print_status() {
    echo -e "${BLUE}🔧 $1${NC}"
}

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

function setup_venv() {
    print_status "Configurando entorno virtual..."
    
    cd "$PROJECT_DIR"
    
    if [ ! -d "$VENV_DIR" ]; then
        print_status "Creando entorno virtual con Python 3.11..."
        python3.11 -m venv .venv
        
        if [ $? -eq 0 ]; then
            print_success "Entorno virtual creado"
        else
            print_error "Error creando entorno virtual"
            exit 1
        fi
    else
        print_success "Entorno virtual ya existe"
    fi
    
    # Activar entorno virtual
    source .venv/bin/activate
    
    # Instalar dependencias
    print_status "Instalando dependencias..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "Entorno virtual configurado exitosamente"
}

function activate_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Entorno virtual no encontrado. Ejecuta 'setup' primero."
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    source .venv/bin/activate
    print_success "Entorno virtual activado"
    echo -e "${BLUE}📍 Proyecto: $PROJECT_DIR${NC}"
    echo -e "${BLUE}🐍 Python: $(python --version)${NC}"
}

function run_scraping() {
    activate_venv
    
    print_status "Ejecutando análisis de scraping..."
    cd packages/scraper/src
    
    echo "1. Analizando PDFs..."
    python simple_pdf_analyzer.py
    
    echo -e "\n2. Procesando enlaces..."
    python simple_links_processor.py
    
    echo -e "\n3. Generando reporte comprensivo..."
    python comprehensive_report.py
    
    print_success "Análisis completado. Revisa los archivos generados:"
    ls -la *.csv *.json
}

function run_backend() {
    activate_venv
    
    print_status "Iniciando servidor backend FastAPI..."
    cd apps/backend
    
    if [ ! -f ".env" ]; then
        print_warning "Archivo .env no encontrado. Creando uno básico..."
        cat > .env << EOF
DATABASE_URL=postgresql://user:password@localhost/tramites_ai
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
DEBUG=True
EOF
    fi
    
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

function show_help() {
    echo -e "${BLUE}🚀 Trámites AI - Script de Desarrollo${NC}"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  setup     - Configura el entorno virtual e instala dependencias"
    echo "  activate  - Activa el entorno virtual"
    echo "  scraping  - Ejecuta el análisis completo de scraping"
    echo "  backend   - Inicia el servidor backend FastAPI"
    echo "  help      - Muestra esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 setup     # Configuración inicial"
    echo "  $0 scraping  # Ejecutar análisis de datos"
    echo "  $0 backend   # Iniciar servidor"
}

# Main
case "${1:-help}" in
    "setup")
        setup_venv
        ;;
    "activate")
        activate_venv
        ;;
    "scraping")
        run_scraping
        ;;
    "backend")
        run_backend
        ;;
    "help"|*)
        show_help
        ;;
esac
