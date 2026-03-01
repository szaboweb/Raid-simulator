import json
import os
from typing import Any, Dict, List
from urllib.parse import quote

from .io import load_data


def build_simulation_preview(out_path: str) -> tuple[str, str | None]:
    if not os.path.exists(out_path):
        return "Még nincs szimulációs fájl. Futtasd a szimulációt a fenti gombbal.", None

    try:
        data = load_data(out_path)
    except Exception as error:
        return "", f"Nem sikerült beolvasni a szimulációs fájlt: {error}"

    if isinstance(data, list):
        preview_data = data[:5]
        suffix = ""
        if len(data) > 5:
            suffix = f"\n\n... további {len(data) - 5} kör a fájlban ({out_path})"
        return json.dumps(preview_data, indent=2, ensure_ascii=False) + suffix, None

    return json.dumps(data, indent=2, ensure_ascii=False), None


def build_excel_embed_url(web_url: str | None) -> str | None:
    if not web_url:
        return None
    return f"https://view.officeapps.live.com/op/embed.aspx?src={quote(web_url, safe='')}"


def build_turn_order_rows(out_path: str, max_rows: int = 500) -> tuple[List[Dict[str, Any]], str | None]:
    if not os.path.exists(out_path):
        return [], None

    try:
        data = load_data(out_path)
    except Exception as error:
        return [], f"Nem sikerült beolvasni a turn adatokat: {error}"

    if not isinstance(data, list):
        return [], "A szimulációs fájl formátuma nem megfelelő a turn táblához."

    rows: List[Dict[str, Any]] = []
    global_turn = 0
    for round_data in data:
        round_no = round_data.get("round") if isinstance(round_data, dict) else None
        events = round_data.get("events", []) if isinstance(round_data, dict) else []
        for turn_in_round, event in enumerate(events, start=1):
            rows.append(
                {
                    "global_turn": global_turn,
                    "round": round_no,
                    "turn_in_round": turn_in_round,
                    "actor": event.get("actor", ""),
                    "ability": event.get("ability", "A1"),
                    "target": event.get("target", ""),
                    "damage": event.get("dmg", 0),
                }
            )
            global_turn += 1

    return rows[:max_rows], None
