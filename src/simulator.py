import argparse
import json
import random
from typing import List, Dict, Any

from .models import Boss, TeamMember, Character
from .io import load_data, save_data


def build_boss(d: Dict[str, Any]) -> Boss:
    abilities = d.get("abilities", {})
    return Boss(
        name=d.get("name", "Boss"),
        hp=int(d.get("hp", 10000)),
        max_hp=int(d.get("hp", 10000)),
        atk=int(d.get("atk", 1000)),
        defense=int(d.get("defense", 0)),
        speed=int(d.get("speed", 100)),
        crit_rate=float(d.get("crit_rate", 0.0)),
        crit_damage=float(d.get("crit_damage", 1.5)),
        skill_multiplier=float(d.get("skill_multiplier", 1.0)),
        abilities=abilities,
    )


def build_team(rows: List[Dict[str, Any]]) -> List[TeamMember]:
    team = []
    for r in rows:
        team.append(
            TeamMember(
                name=r.get("name", "Hero"),
                hp=int(r.get("hp", 5000)),
                max_hp=int(r.get("hp", 5000)),
                atk=int(r.get("atk", 800)),
                defense=int(r.get("defense", 0)),
                speed=int(r.get("speed", 100)),
                crit_rate=float(r.get("crit_rate", 0.0)),
                crit_damage=float(r.get("crit_damage", 1.5)),
                skill_multiplier=float(r.get("skill_multiplier", 1.0)),
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


def run_simulation(boss: Boss, team: List[TeamMember], rounds=50) -> List[Dict[str, Any]]:
    log: List[Dict[str, Any]] = []
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
                # simple damage calculation, check abilities that modify boss damage
                dmg = calc_damage(actor, target)
                target.take_damage(dmg)
                per_char[actor.name]["damage_done"] = per_char[actor.name].get("damage_done", 0) + dmg
                round_summary["events"].append({"actor": actor.name, "target": target.name, "dmg": dmg})
            else:
                # team member attacks boss
                if not boss.alive:
                    break
                dmg = calc_damage(actor, boss)
                # apply boss ability that modifies damage taken
                dmg_multiplier = 1.0
                for ab in boss.abilities.get("on_take_damage", []):
                    if ab.get("type") == "damage_multiplier":
                        dmg_multiplier *= float(ab.get("value", 1.0))
                dmg = int(dmg * dmg_multiplier)
                boss.take_damage(dmg)
                per_char[actor.name]["damage_done"] = per_char[actor.name].get("damage_done", 0) + dmg
                round_summary["events"].append({"actor": actor.name, "target": boss.name, "dmg": dmg})

        # end of round summary
        round_summary["boss_hp"] = boss.hp
        round_summary["team"] = [
            {"name": t.name, "hp": t.hp, "alive": t.alive, "damage_done": per_char.get(t.name, {}).get("damage_done", 0)}
            for t in team
        ]
        log.append(round_summary)
        # stop early if boss dead or all team dead
        if not boss.alive or not any(t.alive for t in team):
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
