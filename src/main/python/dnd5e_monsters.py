import dataclasses
import math

import dice

import character_sheet
from equipment import Armor
from equipment import Weapon


@dataclasses.dataclass
class CharacterSheet5:
    name: str = ""
    str: int = 0
    dex: int = 0
    con: int = 0
    int: int = 0
    wis: int = 0
    cha: int = 0
    armor_class: int = 0
    _hp: str = ""
    xp: int = 0
    vulnerability: str = ""
    resist: str = ""
    special: str = ""
    desc: str = ""
    weapon: Weapon | None = None
    attack_bonus: int = 0
    damage: str = ""
    damage_bonus: int = 0
    armor_worn: Armor | None = None

    def __str__(self) -> str:
        _ = ""
        _ += f"Warrior: {self.warrior}, Rogue: {self.rogue}, Mage: {self.mage}"
        _ += f", HP: {self.hp}, Base Defense: {self.base_defense}, Armor: {self.armor_class}"
        _ += f"\n"
        _ += f"Attack: {self.weapon} ({self.attack_bns:+})"
        _ += f", Damage: {self.damage}"
        return _

    @property
    def attack_bns(self) -> int:
        return self.attack_bonus // 3

    @property
    def base_defense(self) -> int:
        base_defense: int = 4 + (self.warrior + self.rogue) // 2
        return base_defense

    @property
    def warrior(self) -> int:
        return (self.str + self.dex + self.con) // 12

    @property
    def rogue(self) -> int:
        return (self.dex + self.int + self.cha) // 12

    @property
    def mage(self) -> int:
        return (self.int + self.wis + self.cha) // 12

    @property
    def hp(self) -> int:
        if self._hp:
            return max(int(dice.roll(self._hp)), 1)
        return self.warrior + 6

    @hp.setter
    def hp(self, hp: int) -> None:
        self._hp = hp

    @property
    def armor_bns(self) -> int:
        return math.ceil(self.armor_class / 2) - self.base_defense


def from_dnd5e(dnd: CharacterSheet5):
    sheet: character_sheet.CharacterSheet = character_sheet.CharacterSheet()
    sheet.name = dnd.name
    sheet.base_defense = dnd.base_defense
    sheet.warrior_base = dnd.warrior
    sheet.rogue_base = dnd.rogue
    sheet.mage_base = dnd.mage
    sheet.name = dnd.name
    sheet.armor_mod = dnd.armor_bns
    sheet.xp = dnd.xp
    sheet.reset_pools()
    if dnd.hp:
        sheet.hit_points_max = dnd.hp
        sheet.hp = dnd.hp
    if dnd.weapon is not None:
        dnd.weapon.attack_bonus = math.ceil(dnd.weapon.attack_bonus / 2)
        dnd.weapon.damage_bonus = math.ceil(dnd.weapon.damage_bonus / 2)
        sheet.equip_weapon(dnd.weapon)

    sheet.description = dnd.desc
    if dnd.vulnerability:
        sheet.description += f", Vulnerability: {dnd.vulnerability}"
    if dnd.resist:
        sheet.description += f", Resists: {dnd.resist}"
    if dnd.special:
        sheet.description += f", Special: {dnd.special}"
    sheet.fate = 0
    return sheet
