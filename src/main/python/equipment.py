import random
from dataclasses import dataclass

import gamebook_core
from skills import CharacterSkill
from skills import CharacterSkillsList


@dataclass(slots=True)
class Shield(gamebook_core.Item):
    _name: str = ""
    location: str = ""
    defense_bonus: int = 0
    armor_penalty: int = 0
    cost_sp: int = 0

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def base_name(self) -> str:
        return self._name

    def __init__(self, name: str, defense_bonus: int, armor_penalty: int, cost_sp: int):
        self.name = name
        self.defense_bonus = defense_bonus
        self.armor_penalty = armor_penalty
        self.cost_sp = cost_sp

    def __str__(self) -> str:
        name: str = f"{self.name}, Defense: +{self.defense_bonus}, Mana: -{self.armor_penalty}"
        if hasattr(self, 'location') and self.location:
            return f"{name} <{self.location}>"
        return name

    def set_location(self, location: str) -> "Shield":
        self.location = location
        return self

    def with_location(self, location: str) -> "Shield":
        self.location = location
        return self

    @classmethod
    def list(cls) -> list["Shield"]:
        shields: list["Shield"] = list()
        shields.append(Shield("Small Shield", 1, 2, 5))
        shields.append(Shield("Large Shield", 2, 4, 12))
        shields.append(Shield("Tower Shield", 3, 6, 15))
        return shields

    @classmethod
    def by_name(cls, name: str) -> "Shield":
        shields = cls.list()
        for shield in shields:
            if name.lower() in shield.name.lower():
                return shield
        return shields[0]


_item_counter: dict[str, int] = dict()


def item_counter() -> dict[str, int]:
    global _item_counter
    return _item_counter


@dataclass(slots=True)
class Item(gamebook_core.Item):
    _uses: int | None = None
    _name: str = ""
    _desc: str = ""
    location: str = ""
    cost_sp: int = 0

    @property
    def base_name(self) -> str:
        return self._name

    @classmethod
    def _counter(cls, name: str) -> str:
        global _item_counter
        if name not in _item_counter:
            _item_counter[name] = 0
        _item_counter[name] = _item_counter[name] + 1
        return f"{name} (#{_item_counter[name]})"

    def __init__(self, name: str, location: str = "", cost_sp: int = 0):
        global _item_counter
        self._name = Item._counter(name)
        self._desc = ""
        self.location = location
        self.cost_sp = cost_sp
        self._uses = None

    def __str__(self) -> str:
        return self.name

    def set_location(self, location: str) -> "Item":
        return self.with_location(location)

    def with_location(self, location: str) -> "Item":
        self.location = location
        return self

    def with_new_name(self, name: str) -> "Item":
        self._name = self._counter(name)
        return self

    @property
    def description(self) -> str:
        if self._desc:
            return f"\n{self.name}\n{self._desc}".replace("\n", '\n;## ')
        return f"\n;## {self.name}"

    @description.setter
    def description(self, desc: str) -> None:
        self._desc = desc

    @property
    def uses(self) -> int:
        if self._uses is None:
            return 0
        return self._uses

    @uses.setter
    def uses(self, uses: int) -> None:
        self._uses = uses

    @property
    def name(self) -> str:
        x: str = "" if self._uses is None else f" Uses: {self._uses}"
        if hasattr(self, 'location') and self.location:
            return f"{self._name}{x} <loc:{self.location}>"
        return f"{self._name}{x}"

    @name.setter
    def name(self, name: str) -> None:
        if "#" in name:
            self._name = name
        else:
            self._name = Item._counter(name)

    @classmethod
    def list(cls) -> list["Item"]:
        items: list["Item"] = list()
        items.append(Item("Adventurer's Kit", "", 5))
        items.append(Item("Backpack", "", 4))
        items.append(Item("Cask of Beer", "", 6))
        items.append(Item("Cask of Wine", "", 9))
        items.append(Item("Donkey", "", 25))
        items.append(Item("Iron Rations (1 week)", "", 14))
        items.append(Item("Lantern", "", 5))
        items.append(Item("Lock Pick", "", 2))
        items.append(Item("Noble's Clothing", "", 12))
        items.append(Item("Common Clothing", "", 3))
        items.append(Item("Ox Cart", "", 7))
        items.append(Item("Packhorse", "", 30))
        items.append(Item("Pickaxe", "", 3))
        items.append(Item("Pole (3 Yard)", "", 1))
        items.append(Item("Rations (1 week)", "", 7))
        items.append(Item("Riding Horse", "", 75))
        items.append(Item("Rope (10 yards)", "", 2))
        items.append(Item("Saddle Bags, Saddle, and Bridle", "", 8))
        items.append(Item("Torch", "", 1))
        items.append(Item("Travel Clothing", "", 5))
        items.append(Item("Warhorse", "", 150))
        items.append(Item("Spellbook", "", 20))
        return items


@dataclass(slots=True)
class Armor(gamebook_core.Item):
    _name: str = ""
    _defense: int = 0
    defense_bonus: int = 0
    mana_bonus: int = 0
    _armor_penalty: int = 0
    cost_sp: int = 0
    location: str = ""
    _desc: str = ""

    def __init__(self, name: str, defense: int, armor_penalty: int, cost_sp: int):
        self.name = name
        self.defense = defense
        self.armor_penalty = armor_penalty
        self.cost_sp = cost_sp
        self.location = ""
        self.mana_bonus = 0
        self.defense_bonus = 0
        self._desc = ""

    def __str__(self) -> str:
        return self.name

    @property
    def description(self) -> str:
        if self._desc:
            return f"\n{self.name}\n{self._desc}".replace("\n", '\n;## ')
        return self.name

    @description.setter
    def description(self, desc: str) -> None:
        self._desc = desc

    @property
    def defense(self) -> int:
        return self.defense_bonus + self._defense

    @defense.setter
    def defense(self, defense: int) -> None:
        self._defense = defense

    @property
    def armor_penalty(self) -> int:
        return max(self._armor_penalty - self.mana_bonus, 0)

    @armor_penalty.setter
    def armor_penalty(self, penalty: int):
        self._armor_penalty = penalty

    @property
    def base_name(self) -> str:
        return self._name

    @property
    def name(self) -> str:
        _: str = f"{self._name}, Defense: +{self.defense}, Mana: -{self.armor_penalty}"
        if hasattr(self, "location") and self.location:
            return f"{_} <loc:{self.location}>"
        return _

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    def set_location(self, location: str) -> "Armor":
        self.location = location
        return self

    def with_location(self, location: str) -> "Item":
        self.location = location
        return self

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
            if name.lower() in armor._name.lower():
                return armor
        return cls.list()[0]


class Weapon(gamebook_core.Item):
    _name: str = ""
    location: str = ""
    skill: CharacterSkill = None
    _damage: str = "1d6"
    cost_sp: int = 1
    _desc: str = ""
    _attack_bonus: int = 0
    _damage_bonus: int = 0
    _two_handed: bool = False

    def set_location(self, location: str) -> "Weapon":
        self.location = location
        return self

    def with_location(self, location: str) -> "Weapon":
        self.location = location
        return self

    @property
    def description(self) -> str:
        if not hasattr(self, "_desc"):
            setattr(self, "_desc", None)
        if self._desc:
            return f"\n{self.name}\n{self._desc}".replace("\n", '\n;## ')
        return self.name

    @description.setter
    def description(self, desc: str) -> None:
        self._desc = desc

    @property
    def _description(self) -> str:
        if self._desc:
            return f"\n{self.name}\n{self._desc}".replace("\n", '\n;## ')
        return self.name

    @_description.setter
    def _description(self, desc: str) -> None:
        self._desc = desc

    @property
    def name(self) -> str:
        two: str = " Two-handed." if self.two_handed else ""
        _: str = f"{self._name} ({self.attack_bonus:+}/{self.damage_bonus:+}).{two}"
        if hasattr(self, "location") and self.location:
            return f"{_} <loc:{self.location}>"
        return _

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def damage(self) -> str:
        if not hasattr(self, "_damage_bonus"):
            setattr(self, "_damage_bonus", 0)
        return f"{self._damage}{self._damage_bonus:+}"

    @property
    def two_handed(self) -> bool:
        if not hasattr(self, "_two_handed"):
            setattr(self, "_two_handed", False)
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

    @property
    def base_name(self) -> str:
        return self._name

    def __init__(self, name: str,  #
                 skill: CharacterSkill = CharacterSkillsList.skill_by_name("Unarmed"),  #
                 base_damage: str = "1d4x",  #
                 cost_sp: int = 0,  #
                 two_handed: bool = False):
        self._name = name
        self.location = ""
        self.skill = skill
        self._damage = base_damage
        self.cost_sp = cost_sp
        self._desc = ""
        self._description = ""
        self._attack_bonus = 0
        self._damage_bonus = 0
        self._two_handed = two_handed

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
            if weapon._name.lower() == name.lower():
                return weapon
        return random.choice(Weapon.list())

    @classmethod
    def random(cls) -> "Weapon":
        return random.choice(cls.list())

    @classmethod
    def list(cls) -> list["Weapon"]:
        weapons: list["Weapon"] = list()
        weapons.append(Weapon("Axe", CharacterSkillsList.skill_by_name("Axes"), "1d6x", 5))
        weapons.append(Weapon("Bow", CharacterSkillsList.skill_by_name("Bows"), "1d6x", 4, two_handed=True))
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
