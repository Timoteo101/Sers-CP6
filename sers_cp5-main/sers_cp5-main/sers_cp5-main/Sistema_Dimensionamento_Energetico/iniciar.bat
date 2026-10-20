
@echo off
cd /d "%~dp0"
title Sistema de Dimensionamento Energetico

echo ========================================
echo   SISTEMA DE DIMENSIONAMENTO ENERGETICO
echo ========================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERRO: Python nao foi encontrado.
        echo Instale o Python 3 no computador.
        echo https://www.python.org/downloads/
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python"
) else (
    set "PYTHON_CMD=py -3"
)

if not exist ".venv\Scripts\python.exe" (
    echo Preparando o ambiente pela primeira vez...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo Erro ao criar o ambiente Python.
        pause
        exit /b 1
    )

    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt

    if errorlevel 1 (
        echo Erro ao instalar as bibliotecas.
        pause
        exit /b 1
    )
)

echo Iniciando o sistema...
".venv\Scripts\python.exe" -m streamlit run app.py

pause
