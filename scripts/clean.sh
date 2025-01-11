#!/bin/bash

echo "Czyszczenie środowiska..."

# Usuwanie środowiska wirtualnego
if [ -d "../venv" ]; then
    rm -rf ../venv
    echo "Usunięto środowisko wirtualne"
fi

# Usuwanie plików cache Pythona
find .. -type d -name "__pycache__" -exec rm -rf {} +
find .. -type f -name "*.pyc" -delete
find .. -type f -name "*.pyo" -delete
find .. -type f -name "*.pyd" -delete

# Usuwanie plików tymczasowych
find .. -type f -name "*.log" -delete
find .. -type f -name "*.tmp" -delete
find .. -type f -name ".DS_Store" -delete

echo "Czyszczenie zakończone!" 