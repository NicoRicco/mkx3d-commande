@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Interface MKX3D

where python >nul 2>nul
if errorlevel 1 (
    echo Python n'est pas installe.
    echo Installe-le depuis https://www.python.org/downloads/
    echo en cochant la case "Add python.exe to PATH", puis relance ce fichier.
    pause
    exit /b 1
)

echo Verification des modules Python...
python -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo Installation des modules impossible : verifie la connexion Internet.
    pause
    exit /b 1
)

echo.
echo L'interface va s'ouvrir dans le navigateur.
echo Laisse cette fenetre ouverte : la fermer arrete l'interface.
echo.
start "" http://localhost:8080
python serveur\app.py %*
pause
