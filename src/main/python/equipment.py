from dataclasses import dataclass
from enum import Enum

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
    cost_sp: int = 0

    def __init__(self, name: str, cost_sp: int):
        self.name = name
        self.cost_sp = cost_sp

    def __str__(self) -> str:
        return f"{self.name}"

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


@dataclass(slots=True)
class Weapon:
    name: str = ""
    skill: CharacterSkill = None
    damage: str = "1d6"
    cost_sp: int = 1

    def __init__(self, name: str, skill: CharacterSkill, damage: str, cost_sp: int):
        self.name = name
        self.skill = skill
        self.damage = damage
        self.cost_sp = cost_sp

    @classmethod
    def list(cls) -> list["Weapon"]:
        weapons: list["Weapon"] = list()
        weapons.append(Weapon("Axe", CharacterSkillsList.skill_by_name("Axes"), "1d6", 5))
        weapons.append(Weapon("Bow", CharacterSkillsList.skill_by_name("Bows"), "1d6", 4))
        weapons.append(Weapon("Crossbow", CharacterSkillsList.skill_by_name("Bows"), "1d6+3", 8))
        weapons.append(Weapon("Dagger", CharacterSkillsList.skill_by_name("Daggers"), "1d6-2", 2))
        weapons.append(Weapon("Dragon Pistol", CharacterSkillsList.skill_by_name("Firearms"), "1d6+4", 18))
        weapons.append(Weapon("Dragon Rifle", CharacterSkillsList.skill_by_name("Firearms"), "2d6", 25))
        weapons.append(Weapon("Halberd", CharacterSkillsList.skill_by_name("Axes"), "1d6", 7))
        weapons.append(Weapon("Longbow", CharacterSkillsList.skill_by_name("Bows"), "1d6+2", 0))
        weapons.append(Weapon("Mace", CharacterSkillsList.skill_by_name("Blunt"), "1d6", 5))
        weapons.append(Weapon("Spear", CharacterSkillsList.skill_by_name("Thrown"), "1d6", 3))
        weapons.append(Weapon("Staff", CharacterSkillsList.skill_by_name("Blunt"), "1d6", 2))
        weapons.append(Weapon("Sword", CharacterSkillsList.skill_by_name("Swords"), "1d6", 5))
        weapons.append(Weapon("Throwing Star", CharacterSkillsList.skill_by_name("Thrown"), "1d6-2", 2))
        weapons.append(Weapon("Warhammer", CharacterSkillsList.skill_by_name("Blunt"), "1d6", 5))

        return weapons
