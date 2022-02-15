import random
from dataclasses import dataclass

from skills import CharacterSkill
from skills import CharacterSkillsList


@dataclass(slots=True)
class Shield:
    name: str = ""
    defense_bonus: int = 0
    armor_penalty: int = 0
    cost_sp: int = 0

    def __init__(self, name: str, defense_bonus: int, armor_penalty: int, cost_sp: int):
        self.name = name
        self.defense_bonus = defense_bonus
        self.armor_penalty = armor_penalty
        self.cost_sp = cost_sp

    @classmethod
    def list(cls) -> list["Shield"]:
        shields: list["Shield"] = list()
        shields.append(Shield("Small Shield", 1, 2, 5))
        shields.append(Shield("Large Shield", 2, 4, 12))
        shields.append(Shield("Tower Shield", 3, 6, 15))
        return shields


@dataclass(slots=True)
class Item:
    name: str = ""
    location: str = ""
    cost_sp: int = 0

    def __init__(self, name: str, location: str = "", cost_sp: int = 0):
        self.name = name
        self.location = location
        self.cost_sp = cost_sp

    def __str__(self) -> str:
        return f"{self.name} ({self.location})"

    @classmethod
    def list(cls) -> list["Item"]:
        items: list["Item"] = list()
        items.append(Item("Adventurer's Kit", 5))
        items.append(Item("Backpack", 4))
        items.append(Item("Cask of Beer", 6))
        items.append(Item("Cask of Wine", 9))
        items.append(Item("Donkey", 25))
        items.append(Item("Iron Rations (1 week)", 14))
        items.append(Item("Lantern", 5))
        items.append(Item("Lock Pick", 2))
        items.append(Item("Noble's Clothing", 12))
        items.append(Item("Common Clothing", 3))
        items.append(Item("Ox Cart", 7))
        items.append(Item("Packhorse", 30))
        items.append(Item("Pickaxe", 3))
        items.append(Item("Pole (3 Yard)", 1))
        items.append(Item("Rations (1 week)", 7))
        items.append(Item("Riding Horse", 75))
        items.append(Item("Rope (10 yards)", 2))
        items.append(Item("Saddle Bags, Saddle, and Bridle", 8))
        items.append(Item("Torch", 1))
        items.append(Item("Travel Clothing", 5))
        items.append(Item("Warhorse", 150))
        items.append(Item("Spellbook", 20))
        return items


@dataclass(slots=True)
class Armor:
    name: str = ""
    defense: int = 0
    armor_penalty: int = 0
    cost_sp: int = 0

    def __init__(self, name: str, defense: int, armor_penalty: int, cost_sp: int):
        self.name = name
        self.defense = defense
        self.armor_penalty = armor_penalty
        self.cost_sp = cost_sp

    def __str__(self) -> str:
        return f"{self.name}, Defense: +{self.defense}, Mana: -{self.armor_penalty}"

    @classmethod
    def list(cls) -> list["Armor"]:
        armors: list["Armor"] = list()
        armors.append(Armor("Clothes", 0, 0, 3))
        armors.append(Armor("Padded Cloth", 1, 0, 8))
        armors.append(Armor("Leather", 2, 1, 15))
        armors.append(Armor("Scale", 3, 2, 23))
        armors.append(Armor("Lamellar", 4, 3, 35))
        armors.append(Armor("Chain", 5, 4, 70))
        armors.append(Armor("Light Plate", 6, 5, 90))
        armors.append(Armor("Heavy Plate", 7, 5, 120))
        return armors

    @classmethod
    def by_name(cls, name: str) -> "Armor":
        armor: Armor
        for armor in cls.list():
            if name.lower() == armor.name.lower():
                return armor
        return cls.list()[0]


@dataclass(slots=True)
class Weapon:
    name: str = ""
    skill: CharacterSkill = None
    _damage: str = "1d6"
    cost_sp: int = 1
    _description: str = ""
    _attack_bonus: int = 0
    _damage_bonus: int = 0
    _two_handed: bool = False

    @property
    def damage(self) -> str:
        if not hasattr(self, "_damage_bonus"):
            setattr(self, "_damage_bonus", 0)
        return f"{self._damage} + {self._damage_bonus}"

    @property
    def two_handed(self) -> bool:
        return self._two_handed

    @two_handed.setter
    def two_handed(self, two_handed: bool = True):
        self._two_handed = two_handed

    @property
    def damage_bonus(self) -> int:
        if not hasattr(self, "_damage_bonus"):
            setattr(self, "_damage_bonus", 0)
        return self._damage_bonus

    @damage_bonus.setter
    def damage_bonus(self, bonus: int) -> None:
        self._damage_bonus = bonus

    @property
    def attack_bonus(self) -> int:
        if not hasattr(self, "_attack_bonus"):
            setattr(self, "_attack_bonus", 0)
        return self._attack_bonus

    @attack_bonus.setter
    def attack_bonus(self, bonus: int) -> None:
        if not hasattr(self, "_attack_bonus"):
            setattr(self, "_attack_bonus", 0)

        self._attack_bonus = bonus

    def __init__(self, name: str,  #
                 skill: CharacterSkill = CharacterSkillsList.skill_by_name("Unarmed"),  #
                 base_damage: str = "1d4x",  #
                 cost_sp: int = 0,  #
                 two_handed: bool = False):
        self.name = name
        self.skill = skill
        self._damage = base_damage
        self.cost_sp = cost_sp
        self.two_handed = two_handed

    def __str__(self) -> str:
        skill_name: str
        if self.skill:
            skill_name = f"({self.skill.skill_name}) "
        else:
            skill_name = ""
        return f"{self.name} {skill_name}[{self.attack_bonus:+}/attack, {self._damage}{self.damage_bonus:+}/damage]"

    @classmethod
    def by_name(cls, name: str):
        for weapon in Weapon.list():
            if weapon.name.lower() == name.lower():
                return weapon
        return random.choice(Weapon.list())

    @classmethod
    def random(cls) -> "Weapon":
        return random.choice(cls.list())

    @classmethod
    def list(cls) -> list["Weapon"]:
        weapons: list["Weapon"] = list()
        weapons.append(Weapon("Axe", CharacterSkillsList.skill_by_name("Axes"), "1d6x", 5))
        weapons.append(Weapon("Bow", CharacterSkillsList.skill_by_name("Bows"), "1d6x", 4))
        weapons.append(Weapon("Crossbow", CharacterSkillsList.skill_by_name("Bows"), "1d6x+3", 8))
        weapons.append(Weapon("Dagger", CharacterSkillsList.skill_by_name("Daggers"), "1d6x-2", 2))
        weapons.append(Weapon("Dragon Pistol", CharacterSkillsList.skill_by_name("Firearms"), "1d6x+4", 18))
        weapons.append(Weapon("Dragon Rifle", CharacterSkillsList.skill_by_name("Firearms"), "2d6x", 25))
        weapons.append(Weapon("Halberd", CharacterSkillsList.skill_by_name("Axes"), "1d6x", 7))
        weapons.append(Weapon("Longbow", CharacterSkillsList.skill_by_name("Bows"), "1d6x+2", 0))
        weapons.append(Weapon("Mace", CharacterSkillsList.skill_by_name("Blunt"), "1d6x", 5))
        weapons.append(Weapon("Spear", CharacterSkillsList.skill_by_name("Thrown"), "1d6x", 3))
        weapons.append(Weapon("Staff", CharacterSkillsList.skill_by_name("Blunt"), "1d6x", 2))
        weapons.append(Weapon("Sword", CharacterSkillsList.skill_by_name("Swords"), "1d6x", 5))
        weapons.append(Weapon("Throwing Star", CharacterSkillsList.skill_by_name("Thrown"), "1d6x-2", 2))
        weapons.append(Weapon("Warhammer", CharacterSkillsList.skill_by_name("Blunt"), "1d6x", 5))
        two_handed_flame_axe: Weapon = Weapon("Axe (Dark Enchanted)",  #
                                              skill=CharacterSkillsList.skill_by_name("Axes"),  #
                                              base_damage="2d6x",  #
                                              cost_sp=50000,  #
                                              two_handed=True)
        two_handed_flame_axe.attack_bonus = 1
        two_handed_flame_axe.damage_bonus = 1
        two_handed_flame_axe._description = """
The blades are a solid black with red etchings following along their cutting edges.
The hand grip is wrapped in a black leather that is stamped with dark blood red arcane symbols.
The top of the hand grip has a circle of dark blood red leather as does the bottom of the hand grip.
From the edge of the hasp dangles a dark blood red leather strip loop.
Attack Bonus: +1, Damage Bonus: +1, Grants dark sight 60ft.
The blade edges become wreathed in flame when attacking. The +1 effects are from the flames. 
"""
        weapons.append(two_handed_flame_axe)

        return weapons
