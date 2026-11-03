#!/bin/sh
# Lancement de l'interface MKX3D (Linux / macOS)
cd "$(dirname "$0")"
python3 -m pip install --quiet -r requirements.txt || exit 1
echo "Interface : http://localhost:8080  (Ctrl+C pour arrêter)"
(sleep 2; xdg-open http://localhost:8080 2>/dev/null || open http://localhost:8080 2>/dev/null) &
exec python3 serveur/app.py "$@"
