import random
from dataclasses import dataclass
from dataclasses import field
from mana import MageSpell
from skills import CharacterSkill
from skills import SkillAttribute
from talents import CharacterTalent


@dataclass(slots=True)
class CharacterSheet:
    weapon: list[str] = field(default_factory=list)
    armor_worn: list[str] = field(default_factory=list)
    skills: list[CharacterSkill] = field(default_factory=list)
    talents: list[CharacterTalent] = field(default_factory=list)
    spells: list[MageSpell] = field(default_factory=list)

    warrior: int = 0
    rogue: int = 0
    mage: int = 0

    adv_taken: int = 0
    fate: int = 0
    fate_starting: int = 0
    armor_penalty: int = 0

    hit_points_max: int = 0
    mana_max: int = 0
    defense: int = 0

    hit_points: int = 0
    mana: int = 0
    base_defense: int = 0
    armor: int = 0

    def reset_pools(self) -> None:
        self.hit_points_max = 6 + self.warrior
        self.fate_starting = max(self.rogue, 1)
        self.mana_max = self.mage * 2

        self.hit_points = self.hit_points_max
        self.fate = self.fate_starting
        self.mana = self.mana_max

        self.base_defense = 4 + (self.warrior + self.rogue) // 2

    def print(self) -> None:
        print(f"W: {self.warrior}, Adv. Taken: {self.adv_taken}")
        print(f"R: {self.rogue}, Fate: {self.fate}")
        print(f"M: {self.mage}, Armor Penalty: {self.armor_penalty}")
        print()
        print(f"HP: {self.hit_points} ({self.hit_points_max})")
        print(f"Mana: {self.mana} ({self.mana_max})")
        print(f"Defense: {self.defense} = {self.base_defense=} | {self.armor=}")
        print()
        print("=== SKILLS ===")
        for skill in self.skills:
            print(f" - {skill}")
        print()

    def attribute_level(self, skill: SkillAttribute) -> int:
        if skill == SkillAttribute.Rogue:
            return self.rogue
        elif skill == SkillAttribute.Mage:
            return self.mage
        elif skill == SkillAttribute.Warrior:
            return self.warrior

        return 0

