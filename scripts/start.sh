#!/bin/bash

echo "Uruchamianie serwera kamery..."

pwd
# Sprawdzanie czy plik główny istnieje
if [ ! -f "../aegis.camera.handler.py" ]; then
    echo "Błąd: Nie znaleziono pliku aegis.camera.handler"
    exit 1
fi

# Uruchomienie serwera
python3 ../aegis.camera.handler.py

echo "Serwer został zatrzymany."