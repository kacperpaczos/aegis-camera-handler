#!/bin/bash

echo "Uruchamianie serwera kamery..."

# Sprawdzanie czy venv istnieje
if [ ! -d "../venv" ]; then
    echo "Błąd: Nie znaleziono środowiska wirtualnego. Uruchom najpierw install.sh"
    exit 1
fi

# Aktywacja środowiska wirtualnego
source ../venv/bin/activate

# Sprawdzanie czy plik główny istnieje
if [ ! -f "../aegis.camera.handler.py" ]; then
    echo "Błąd: Nie znaleziono pliku aegis.camera.handler.py"
    exit 1
fi

# Uruchomienie serwera
python ../aegis.camera.handler.py

# Dezaktywacja środowiska
deactivate

echo "Serwer został zatrzymany."