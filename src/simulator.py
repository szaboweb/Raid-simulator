import argparse
import json
import random
from typing import List, Dict, Any

from .models import Boss, TeamMember, Character
from .io import load_data, save_data


def normalize_crit_rate(value: float) -> float:
    rate = float(value)
    if rate > 1.0:
        return rate / 100.0
    return max(0.0, rate)


def normalize_crit_damage(value: float) -> float:
    crit_damage = float(value)
    if crit_damage > 3.0:
        return crit_damage / 100.0
    return max(1.0, crit_damage)


def build_boss(d: Dict[str, Any]) -> Boss:
    abilities = d.get("abilities", {})
    extra = {
        "infinite_hp": bool(d.get("infinite_hp", False)),
    }
    return Boss(
        name=d.get("name", "Boss"),
        hp=int(d.get("hp", 10000)),
        max_hp=int(d.get("hp", 10000)),
        atk=int(d.get("atk", 1000)),
        defense=int(d.get("defense", 0)),
        speed=int(d.get("speed", 100)),
        crit_rate=normalize_crit_rate(float(d.get("crit_rate", 0.0))),
        crit_damage=normalize_crit_damage(float(d.get("crit_damage", 1.5))),
        skill_multiplier=float(d.get("skill_multiplier", 1.0)),
        accuracy=int(d.get("accuracy", d.get("acc", 0))),
        resistance=int(d.get("resistance", d.get("res", 0))),
        extra=extra,
        abilities=abilities,
    )


def normalize_member_abilities(row: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    abilities = row.get("abilities", {}) if isinstance(row.get("abilities", {}), dict) else {}

    def ability_def(name: str, default_multiplier: float, default_cooldown: int, default_priority: int) -> Dict[str, float]:
        raw = abilities.get(name, {}) if isinstance(abilities.get(name, {}), dict) else {}
        return {
            "multiplier": float(raw.get("multiplier", default_multiplier)),
            "cooldown": int(raw.get("cooldown", default_cooldown)),
            "priority": int(raw.get("priority", default_priority)),
        }

    a1_default_multiplier = float(row.get("skill_multiplier", 1.0))
    return {
        "A1": ability_def("A1", a1_default_multiplier, 0, 3),
        "A2": ability_def("A2", 1.0, 3, 2),
        "A3": ability_def("A3", 1.0, 4, 1),
        "A4": ability_def("A4", 1.0, 0, 0),
    }


def build_team(rows: List[Dict[str, Any]]) -> List[TeamMember]:
    team = []
    for r in rows:
        member_abilities = normalize_member_abilities(r)
        team.append(
            TeamMember(
                name=r.get("name", "Hero"),
                hp=int(r.get("hp", 5000)),
                max_hp=int(r.get("hp", 5000)),
                atk=int(r.get("atk", 800)),
                defense=int(r.get("defense", 0)),
                speed=int(r.get("speed", 100)),
                crit_rate=normalize_crit_rate(float(r.get("crit_rate", 0.0))),
                crit_damage=normalize_crit_damage(float(r.get("crit_damage", 1.5))),
                skill_multiplier=float(member_abilities["A1"]["multiplier"]),
                accuracy=int(r.get("accuracy", r.get("acc", 0))),
                resistance=int(r.get("resistance", r.get("res", 0))),
                abilities=member_abilities,
            )
        )
    return team


def calc_damage(attacker: Character, defender: Character, extra_multiplier=1.0) -> int:
    base = attacker.atk * attacker.skill_multiplier * extra_multiplier
    reduction = defender.defense / (defender.defense + 1000) if defender.defense else 0
    dmg = max(1, int(base * (1 - reduction)))
    if random.random() < attacker.crit_rate:
        dmg = int(dmg * attacker.crit_damage)
    return dmg


def apply_boss_abilities_on_round_start(boss: Boss, round_no: int):
    for ab in boss.abilities.get("on_round_start", []):
        if ab.get("type") == "heal_percent":
            pct = float(ab.get("value", 0.0))
            heal = int(boss.max_hp * pct)
            boss.hp = min(boss.max_hp, boss.hp + heal)


def choose_ability(member: TeamMember, cooldown_state: Dict[str, int]) -> str:
    available: List[tuple[int, str]] = []
    for ability_name in ("A1", "A2", "A3", "A4"):
        ability_cfg = member.abilities.get(ability_name, {}) if isinstance(member.abilities, dict) else {}
        multiplier = float(ability_cfg.get("multiplier", 1.0))
        if multiplier <= 0:
            continue
        remaining = int(cooldown_state.get(ability_name, 0))
        if remaining <= 0:
            priority = int(ability_cfg.get("priority", 0))
            available.append((priority, ability_name))

    if available:
        available.sort(key=lambda x: (-x[0], x[1]))
        return available[0][1]
    return "A1"


def run_simulation(boss: Boss, team: List[TeamMember], rounds=50) -> List[Dict[str, Any]]:
    log: List[Dict[str, Any]] = []
    boss_cycle = ["AOE1", "AOE2", "STUN"]
    cooldowns: Dict[str, Dict[str, int]] = {
        member.name: {"A1": 0, "A2": 0, "A3": 0, "A4": 0}
        for member in team
    }

    for r in range(1, rounds + 1):
        round_summary = {"round": r, "boss_hp": boss.hp, "events": []}

        apply_boss_abilities_on_round_start(boss, r)

        # build action order by speed (team members + boss)
        actors = [*team, boss]
        actors = [a for a in actors if a.alive]
        actors.sort(key=lambda x: x.speed, reverse=True)

        # per-round per-character stats
        per_char = {a.name: {"hp": a.hp, "damage_done": 0, "alive": a.alive} for a in actors}

        for actor in actors:
            if not actor.alive:
                continue
            if isinstance(actor, Boss):
                # boss attacks a random alive member
                targets = [t for t in team if t.alive]
                if not targets:
                    break
                target = random.choice(targets)
                boss_ability = boss_cycle[(r - 1) % len(boss_cycle)]
                # simple damage calculation, check abilities that modify boss damage
                dmg = calc_damage(actor, target)
                target.take_damage(dmg)
                per_char[actor.name]["damage_done"] = per_char[actor.name].get("damage_done", 0) + dmg
                round_summary["events"].append(
                    {
                        "actor": actor.name,
                        "target": target.name,
                        "dmg": dmg,
                        "ability": boss_ability,
                    }
                )
            else:
                # team member attacks boss
                if not boss.alive:
                    break
                member_cooldowns = cooldowns.setdefault(actor.name, {"A1": 0, "A2": 0, "A3": 0, "A4": 0})
                for key in ("A1", "A2", "A3", "A4"):
                    if member_cooldowns.get(key, 0) > 0:
                        member_cooldowns[key] -= 1

                ability_name = choose_ability(actor, member_cooldowns)
                ability_cfg = actor.abilities.get(ability_name, {}) if isinstance(actor.abilities, dict) else {}
                ability_multiplier = float(ability_cfg.get("multiplier", actor.skill_multiplier))
                dmg = calc_damage(actor, boss, extra_multiplier=ability_multiplier)

                configured_cooldown = int(ability_cfg.get("cooldown", 0))
                member_cooldowns[ability_name] = max(0, configured_cooldown)

                # apply boss ability that modifies damage taken
                dmg_multiplier = 1.0
                for ab in boss.abilities.get("on_take_damage", []):
                    if ab.get("type") == "damage_multiplier":
                        dmg_multiplier *= float(ab.get("value", 1.0))
                dmg = int(dmg * dmg_multiplier)
                if not boss.extra.get("infinite_hp", False):
                    boss.take_damage(dmg)
                per_char[actor.name]["damage_done"] = per_char[actor.name].get("damage_done", 0) + dmg
                round_summary["events"].append(
                    {
                        "actor": actor.name,
                        "target": boss.name,
                        "dmg": dmg,
                        "ability": ability_name,
                    }
                )

        # end of round summary
        round_summary["boss_hp"] = boss.hp
        round_summary["team"] = [
            {"name": t.name, "hp": t.hp, "alive": t.alive, "damage_done": per_char.get(t.name, {}).get("damage_done", 0)}
            for t in team
        ]
        log.append(round_summary)
        # stop early if boss dead or all team dead
        if (not boss.extra.get("infinite_hp", False) and not boss.alive) or not any(t.alive for t in team):
            break

    return log


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--boss", required=True, help="Path to boss file (yaml/json/csv/xlsx)")
    parser.add_argument("--team", required=True, help="Path to team file (yaml/json/csv/xlsx)")
    parser.add_argument("--abilities", required=False, help="Path to boss abilities YAML", default=None)
    parser.add_argument("--out", required=False, help="Output file path", default="battle_log.json")
    parser.add_argument("--rounds", type=int, default=50)
    args = parser.parse_args()

    boss_data = load_data(args.boss)
    team_data = load_data(args.team)

    boss = build_boss(boss_data if isinstance(boss_data, dict) else boss_data[0])
    team = build_team(team_data if isinstance(team_data, list) else [team_data])

    if args.abilities:
        ab = load_data(args.abilities)
        if isinstance(ab, dict):
            boss.abilities.update(ab)

    log = run_simulation(boss, team, rounds=args.rounds)

    save_data(log, args.out)
    print(f"Simulation finished. Saved to {args.out}")


if __name__ == "__main__":
    main()
