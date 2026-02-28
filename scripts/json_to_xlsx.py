import pandas as pd
import json
import sys
import os

# Alapértelmezett bemenet/kimenet
JSON_PATH = sys.argv[1] if len(sys.argv) > 1 else "../battle_log.json"
XLSX_PATH = sys.argv[2] if len(sys.argv) > 2 else "../battle_log.xlsx"

if not os.path.exists(JSON_PATH):
    print(f"Hiba: {JSON_PATH} nem található!")
    sys.exit(1)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Ha a json egy lista, DataFrame-be rakjuk
if isinstance(data, list):
    df = pd.DataFrame(data)
else:
    # Ha dict, próbáljuk a 'log' vagy 'entries' kulcsot
    if "log" in data:
        df = pd.DataFrame(data["log"])
    elif "entries" in data:
        df = pd.DataFrame(data["entries"])
    else:
        df = pd.DataFrame([data])

# Excelbe mentés
try:
    df.to_excel(XLSX_PATH, index=False)
    print(f"Sikeres export: {XLSX_PATH}")
except Exception as e:
    print(f"Hiba az exportáláskor: {e}")
    sys.exit(1)
