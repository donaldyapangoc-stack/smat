@echo off
title Lanzador del Ecosistema SMAT - FISI 2026
echo ====================================================
echo    INICIANDO COMPONENTES DEL SISTEMA SMAT
echo ====================================================

:: 1. Levantar el Backend de FastAPI
echo [1/3] Levantando Servidor Cloud FastAPI...
start "MQTT Bridge" cmd /k "cd iot_device && ..\backend\venv\Scripts\activate && python mqtt_bridge.py"

:: Esperar 3 segundos a que el backend inicialice la base de datos
timeout /t 3 /nobreak > nul

:: 2. Activar el Bridge de Acoplamiento IoT (Semana 11)
echo [2/3] Activando Middleware MQTT Bridge...
start "MQTT Bridge" cmd /k "cd iot_device && ..\backend\venv\Scripts\activate && python mqtt_bridge.py"

:: 3. Abrir el Gemelo Digital compilado en Godot (Semana 13)
echo [3/3] Lanzando Interfaz Grafica de Simulacion...
cd simulation\dist\
start SMAT_Monitor.exe

echo ====================================================
echo ?Todo el ecosistema esta corriendo en simultaneo!
echo ====================================================
pause
