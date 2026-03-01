from typing import Any, Dict, List

MIN_HERO_SLOTS = 10


def normalize_heroes(raw: Any) -> List[Dict[str, Any]]:
    if isinstance(raw, list):
        rows = raw
    elif isinstance(raw, dict):
        rows = [raw]
    else:
        rows = []

    normalized = []
    for row in rows:
        abilities = row.get("abilities", {}) if isinstance(row.get("abilities", {}), dict) else {}
        normalized.append(
            {
                "name": row.get("name", ""),
                "hp": int(row.get("hp", 5000)),
                "atk": int(row.get("atk", 800)),
                "defense": int(row.get("defense", 0)),
                "resistance": int(row.get("resistance", row.get("res", 0))),
                "accuracy": int(row.get("accuracy", row.get("acc", 0))),
                "speed": int(row.get("speed", 100)),
                "crit_rate": float(row.get("crit_rate", 0.0)),
                "crit_damage": float(row.get("crit_damage", 1.5)),
                "a1_priority": int(abilities.get("A1", {}).get("priority", 3)),
                "a1_cooldown": int(abilities.get("A1", {}).get("cooldown", 0)),
                "a2_priority": int(abilities.get("A2", {}).get("priority", 2)),
                "a2_cooldown": int(abilities.get("A2", {}).get("cooldown", 3)),
                "a3_priority": int(abilities.get("A3", {}).get("priority", 1)),
                "a3_cooldown": int(abilities.get("A3", {}).get("cooldown", 4)),
                "a4_priority": int(abilities.get("A4", {}).get("priority", 0)),
                "a4_cooldown": int(abilities.get("A4", {}).get("cooldown", 0)),
                "selected": bool(row.get("selected", False)),
            }
        )
    return normalized


def ensure_min_hero_slots(heroes: List[Dict[str, Any]], min_count: int = MIN_HERO_SLOTS) -> List[Dict[str, Any]]:
    padded = list(heroes)
    while len(padded) < min_count:
        padded.append(
            {
                "name": "",
                "hp": 5000,
                "atk": 800,
                "defense": 0,
                "resistance": 0,
                "accuracy": 0,
                "speed": 100,
                "crit_rate": 0.0,
                "crit_damage": 1.5,
                "a1_priority": 3,
                "a1_cooldown": 0,
                "a2_priority": 2,
                "a2_cooldown": 3,
                "a3_priority": 1,
                "a3_cooldown": 4,
                "a4_priority": 0,
                "a4_cooldown": 0,
                "selected": False,
            }
        )
    return padded


def parse_heroes_from_form(form) -> List[Dict[str, Any]]:
    count = int(form.get("hero_count", 0))
    heroes: List[Dict[str, Any]] = []

    for index in range(count):
        name = form.get(f"hero_{index}_name", "").strip()
        if not name:
            continue

        hero = {
            "name": name,
            "hp": int(form.get(f"hero_{index}_hp", 5000)),
            "atk": int(form.get(f"hero_{index}_atk", 800)),
            "defense": int(form.get(f"hero_{index}_defense", 0)),
            "resistance": int(form.get(f"hero_{index}_resistance", 0)),
            "accuracy": int(form.get(f"hero_{index}_accuracy", 0)),
            "speed": int(form.get(f"hero_{index}_speed", 100)),
            "crit_rate": float(form.get(f"hero_{index}_crit_rate", 0.0)),
            "crit_damage": float(form.get(f"hero_{index}_crit_damage", 1.5)),
            "skill_multiplier": 1.0,
            "abilities": {
                "A1": {
                    "multiplier": 1.0,
                    "priority": int(form.get(f"hero_{index}_a1_priority", 3)),
                    "cooldown": int(form.get(f"hero_{index}_a1_cooldown", 0)),
                },
                "A2": {
                    "multiplier": 1.0,
                    "priority": int(form.get(f"hero_{index}_a2_priority", 2)),
                    "cooldown": int(form.get(f"hero_{index}_a2_cooldown", 3)),
                },
                "A3": {
                    "multiplier": 1.0,
                    "priority": int(form.get(f"hero_{index}_a3_priority", 1)),
                    "cooldown": int(form.get(f"hero_{index}_a3_cooldown", 4)),
                },
                "A4": {
                    "multiplier": 1.0,
                    "priority": int(form.get(f"hero_{index}_a4_priority", 0)),
                    "cooldown": int(form.get(f"hero_{index}_a4_cooldown", 0)),
                },
            },
            "selected": form.get(f"hero_{index}_selected") == "on",
        }
        heroes.append(hero)

    return heroes


def build_selected_team(heroes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "name": h["name"],
            "hp": h["hp"],
            "atk": h["atk"],
            "defense": h["defense"],
            "resistance": h["resistance"],
            "accuracy": h["accuracy"],
            "speed": h["speed"],
            "crit_rate": h["crit_rate"],
            "crit_damage": h["crit_damage"],
            "skill_multiplier": h["skill_multiplier"],
            "abilities": h["abilities"],
        }
        for h in heroes
        if h.get("selected")
    ]
