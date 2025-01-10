#!/bin/bash

echo "Sprawdzanie czy pip jest zainstalowany..."

# Sprawdzanie czy pip jest zainstalowany
if ! command -v pip &> /dev/null; then
    echo "Pip nie jest zainstalowany. Instalowanie pip..."
    
    # Sprawdzanie rodzaju systemu i instalacja pip
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    elif command -v pacman &> /dev/null; then
        sudo pacman -S python-pip
    else
        echo "Nie można zainstalować pip automatycznie. Zainstaluj pip ręcznie."
        exit 1
    fi
fi

echo "Instalowanie wymaganych pakietów..."

# Instalacja wymaganych pakietów
pip install aiohttp
pip install opencv-python
pip install asyncio

echo "Instalacja zakończona pomyślnie!"