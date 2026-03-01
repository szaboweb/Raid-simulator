from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Character:
    name: str
    hp: int
    max_hp: int
    atk: int
    defense: int = 0
    speed: int = 100
    crit_rate: float = 0.0
    crit_damage: float = 1.5
    skill_multiplier: float = 1.0
    accuracy: int = 0
    resistance: int = 0
    alive: bool = True
    extra: Dict[str, Any] = field(default_factory=dict)

    def take_damage(self, dmg: int):
        self.hp = max(0, self.hp - dmg)
        if self.hp == 0:
            self.alive = False


@dataclass
class Boss(Character):
    abilities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TeamMember(Character):
    abilities: Dict[str, Any] = field(default_factory=dict)
