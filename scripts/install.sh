#!/bin/bash

echo "Tworzenie środowiska wirtualnego..."

# Sprawdzanie czy venv jest zainstalowany
if ! command -v python3 -m venv &> /dev/null; then
    echo "Python venv nie jest zainstalowany. Instalowanie..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-venv
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-venv
    elif command -v pacman &> /dev/null; then
        sudo pacman -S python-virtualenv
    else
        echo "Nie można zainstalować venv automatycznie. Zainstaluj ręcznie."
        exit 1
    fi
fi

# Tworzenie środowiska wirtualnego
python3 -m venv venv

# Aktywacja środowiska
source venv/bin/activate

echo "Instalowanie wymaganych pakietów..."

# Aktualizacja pip
pip install --upgrade pip

# Instalacja wymaganych pakietów
pip install aiohttp
pip install opencv-python
pip install asyncio

echo "Instalacja zakończona pomyślnie!"