import random
from dataclasses import dataclass
from dataclasses import field

import dice

from equipment import Armor
from equipment import Item
from equipment import Weapon
from mana import MageSpell
from mana import MageSpellList
from skills import CharacterSkill
from skills import SkillAttribute
from talents import CharacterTalent


@dataclass(slots=True)
class CharacterSheet:
    name: str = ""
    description: str = ""
    weapons: list[Weapon] = field(default_factory=list)
    armor_worn: list[Armor] = field(default_factory=list)
    skills: list[CharacterSkill] = field(default_factory=list)
    talents: list[CharacterTalent] = field(default_factory=list)
    spells: list[MageSpell] = field(default_factory=list)
    equipment: list[Item] = field(default_factory=list)

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

    _hit_points: int = 0
    mana: int = 0
    base_defense: int = 0
    armor: int = 0
    hit_points_armor: int = 0

    @property
    def attack(self) -> int:
        bonus: int = 0
        if self.weapons:
            bonus = self.weapons[0].attack_bonus
        return self.warrior + bonus

    @property
    def damage(self) -> str:
        damage: str = "1d2"
        if self.weapons:
            weapon: Weapon = self.weapons[0]
            damage = weapon.damage
        return damage

    @property
    def hit_points(self) -> int:
        return self._hit_points

    @hit_points.setter
    def hit_points(self, hit_points: int):
        self._hit_points = min(self.hit_points_max, hit_points)

    @property
    def weapon(self) -> Weapon:
        if not self.weapons:
            return Weapon("")
        return self.weapons[0]

    @property
    def hps(self) -> tuple[int, int]:
        return self.hit_points, self.hit_points_armor

    @hps.setter
    def hps(self, hit_points: tuple[int, int]) -> None:
        self.hit_points, self.hit_points_armor = hit_points

    def reset_pools(self) -> None:
        self.hit_points_max = 6 + self.warrior
        self.fate_starting = max(self.rogue, 1)
        self.mana_max = self.mage * 2

        self.hit_points = self.hit_points_max
        self.fate = self.fate_starting
        self.mana = self.mana_max - self.armor_penalty

        self.base_defense = 4 + (self.warrior + self.rogue) // 2
        self.defense = self.base_defense

    def reset_armor_penalty(self) -> str:
        self.mana += self.armor_penalty
        if self.mana > self.mana_max:
            self.mana = self.mana_max
        self.armor_penalty = 0
        return f"Mana: {self.mana}/{self.mana_max}"

    def equip_weapon(self, new_weapon: Weapon) -> tuple[str, int, int]:
        for weapon in self.weapons.copy():
            if weapon.name.lower() == new_weapon.name.lower():
                self.weapons.remove(weapon)
        self.weapons.insert(0, new_weapon)
        return new_weapon.name, new_weapon.attack_bonus, new_weapon.damage_bonus

    def set_armor(self, defense: int, penalty: int) -> str:
        self.armor = defense
        self.armor_penalty = penalty
        self.mana = min(self.mana_max - self.armor_penalty, self.mana)
        self.hit_points_armor = 5 * self.armor
        return f"Armor: {self.armor}, Armor Penalty: {self.armor_penalty}, Mana: {self.mana}"

    def equip_armor(self, armor: Armor) -> str:
        return self.set_armor(armor.defense, armor.armor_penalty)

    def print(self) -> None:
        print(f"Warrior: {self.warrior}, Adv. Taken: {self.adv_taken}")
        print(f"Rogue: {self.rogue}, Fate: {self.fate}")
        print(f"Mage: {self.mage}, Armor Penalty: {self.armor_penalty}")
        print()
        print(f"HP: {self.hit_points} ({self.hit_points_max})")
        print(f"Mana: {self.mana} ({self.mana_max})")
        print(f"Defense: {self.defense} = {self.base_defense=} | {self.armor=}")
        print()

        print("=== SKILLS ===")
        for skill in self.skills:
            print(f" - {skill}")
        print()

        print("=== TALENTS ===")
        for talent in self.talents:
            print(f" - {talent}")
        print()

        print("=== SPELLS ===")
        if not self.spells:
            print("None")
        for spell in self.spells:
            print(f" - {spell}")
        print()

        print("=== EQUIPMENT ===")
        if not self.equipment:
            print("None")
        for item in self.equipment:
            print(f" - {item}")
        print()

        print("=== WEAPONS ===")
        if not self.weapons:
            print("None")
        for item in self.weapons:
            print(f" - {item}")
        print()

        print("=== ARMOR ===")
        if not self.armor_worn:
            print("None")
        for item in self.armor_worn:
            print(f" - {item}")
        print()

    def attribute_level(self, skill: SkillAttribute) -> int:
        if skill == SkillAttribute.Rogue:
            return self.rogue
        elif skill == SkillAttribute.Mage:
            return self.mage
        elif skill == SkillAttribute.Warrior:
            return self.warrior

        return 0

    def skill_names(self) -> list[str]:
        skills: list[str] = list()
        for skill in self.skills:
            skills.append(skill.skill_name)
        return skills

    def cast(self, spell_name: str, mana_burn: bool = False) -> str:
        if not self.spells:
            return "No spells."
        for spell in self.spells:
            if spell.name.lower() == spell_name.lower():
                if self.mana < spell.mana_cost:
                    return f"Not enough mana ({self.mana}) for {spell.name} ({spell.mana_cost})"
                roll: int = dice.roll(f"1d6 + {self.mage}")
                if roll < spell.difficulty.value:
                    return f"Cast failed. {roll} < {spell.difficulty.name} {spell.difficulty.value}"
                self.mana -= spell.mana_cost
                return f"Cast succeeded. {spell.name}: {spell.description}"
        return "That spell is not available."

    def spell_list(self) -> list[str]:
        spells: list[str] = list()
        for spell in self.spells:
            spells.append(f"{spell.name}: {spell.difficulty.name}, Mana: {spell.mana_cost:,}")
        return spells

    def spell_add(self, name: str) -> MageSpell:
        new_spell: MageSpell = MageSpellList.spell_by_name(name)
        for spell in self.spells:
            if name.lower() == spell.name.lower():
                return spell
        self.spells.append(new_spell)
        return new_spell
