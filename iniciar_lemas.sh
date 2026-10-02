#!/usr/bin/env bash
# Continuidad estudiantil LEMAS - modo institucional en macOS o Linux (solo en este equipo).
# Uso: bash iniciar_lemas.sh
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
    echo "Preparando la aplicación por primera vez. Puede tardar unos minutos..."
    python3 -m venv .venv
    .venv/bin/python -m pip install --upgrade pip
    .venv/bin/python -m pip install -r app/requirements.txt
fi
export LEMAS_MODO=institucional
echo "Abriendo la aplicación en http://localhost:8501 (los datos se procesan solo en este equipo)"
exec .venv/bin/python -m streamlit run app/app.py --server.address 127.0.0.1 \
    --server.port 8501 --browser.gatherUsageStats false
