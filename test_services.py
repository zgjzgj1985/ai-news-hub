# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests

# Test Ollama
try:
    r = requests.get('http://localhost:11434/api/tags', timeout=5)
    print(f"Ollama status: {r.status_code}")
    data = r.json()
    models = [m.get('name', '') for m in data.get('models', [])]
    print(f"Models: {models}")
except Exception as e:
    print(f"Ollama error: {e}")

# Test backend
try:
    r = requests.get('http://localhost:8000/health', timeout=5)
    print(f"Backend status: {r.status_code}")
    print(f"Backend response: {r.text}")
except Exception as e:
    print(f"Backend error: {e}")
