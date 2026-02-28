import json
import os
from typing import Any

import pandas as pd
import yaml


def load_data(path: str) -> Any:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".yml", ".yaml"):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    if ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    if ext == ".csv":
        df = pd.read_csv(path)
        return df.to_dict(orient="records")
    if ext in (".xls", ".xlsx"):
        df = pd.read_excel(path)
        return df.to_dict(orient="records")
    raise ValueError(f"Unsupported extension: {ext}")


def save_data(data: Any, path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".yml", ".yaml"):
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
        return
    if ext == ".json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return
    # For CSV / Excel try to build a dataframe
    try:
        df = pd.json_normalize(data)
    except Exception:
        df = pd.DataFrame(data)

    if ext == ".csv":
        df.to_csv(path, index=False)
        return
    if ext in (".xls", ".xlsx"):
        df.to_excel(path, index=False)
        return
    raise ValueError(f"Unsupported extension: {ext}")
