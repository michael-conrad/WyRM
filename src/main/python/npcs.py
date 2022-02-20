import copy

import jsonpickle

from character_sheet import CharacterSheet
from equipment import Weapon
from skills import CharacterSkillsList
from skills import SkillAttribute


class NPC:
    _counter_: dict[str, int] = dict()

    @classmethod
    def _counter(cls, name: str) -> str:
        if name not in cls._counter_:
            cls._counter_[name] = 0
        cls._counter_[name] = cls._counter_[name] + 1
        return f"{name} (#{cls._counter_[name]})"

    @classmethod
    def giant_beetle(cls) -> CharacterSheet:
        sheet = CharacterSheet()
        sheet.name = NPC._counter("Giant Beetle")
        sheet.warrior_base = 4
        sheet.rogue_base = 4
        sheet.mage_base = 0
        sheet.armor = 3
        bite: Weapon = Weapon("Bite", CharacterSkillsList.skill_by_name("Unarmed"), "1d6", 0)
        sheet.weapons.append(bite)
        sheet.reset_pools()
        sheet.base_defense = 8 - sheet.armor
        sheet.hit_points_max = 14
        sheet.hp = 14  
        return sheet

    @classmethod
    def skeleton_warrior(cls) -> CharacterSheet:
        sheet = CharacterSheet()
        sheet.name = NPC._counter("Skeleton Warrior")
        sheet.description = "Rusted armor. Broken shield. Short sword."
        sheet.warrior_base = 3
        sheet.rogue_base = 3
        sheet.mage_base = 0
        sheet.armor = 1
        sword: Weapon = copy.copy(Weapon.by_name("Sword"))
        sword.name = "Sword - Rusty"
        sheet.weapons.append(sword)
        sheet.reset_pools()
        sheet.base_defense = 7 - sheet.armor
        sheet.hit_points_max = 9
        sheet.hp = 9  
        return sheet

    @classmethod
    def skeleton_archer(cls) -> CharacterSheet:
        sheet = CharacterSheet()
        sheet.name = NPC._counter("Skeleton Archer")
        sheet.description = "Rusted armor. Bow. 10 Arrows."
        sheet.warrior_base = 3
        sheet.rogue_base = 3
        sheet.mage_base = 0
        sheet.armor = 1
        wpn: Weapon = Weapon.by_name("Bow")
        wpn.name = "Bow - Dry rotting"
        sheet.weapons.append(wpn)
        sheet.reset_pools()
        sheet.base_defense = 7 - sheet.armor
        sheet.hit_points_max = 9
        sheet.hp = 9  
        return sheet

    @classmethod
    def zombie(cls) -> CharacterSheet:
        sheet = CharacterSheet()
        sheet.name = NPC._counter("Zombie")
        sheet.description = "Those bitten and killed by a zombie arise as zombies in 1d6 minutes each."
        sheet.warrior_base = 6
        sheet.rogue_base = 0
        sheet.mage_base = 0
        sheet.armor = 0
        wpn: Weapon = Weapon(name="Infected Bite", base_damage="1d6x")
        sheet.weapons.append(wpn)
        sheet.reset_pools()
        sheet.base_defense = 7
        sheet.hit_points_max = 12
        sheet.hp = 12  
        return sheet

    @classmethod
    def giant_rat(cls) -> CharacterSheet:
        sheet = CharacterSheet()
        sheet.name = NPC._counter("Giant Rat")
        sheet.description = "Bites. 1d6."
        sheet.warrior_base = 4
        sheet.rogue_base = 2
        sheet.mage_base = 0
        sheet.armor = 0
        wpn: Weapon = Weapon(name="Bite (Warrior)", base_damage="1d6x")
        sheet.weapons.append(wpn)
        sheet.reset_pools()
        sheet.base_defense = 7
        sheet.hit_points_max = 12
        sheet.hp = 12  
        return jsonpickle.decode(jsonpickle.encode(sheet))

    @classmethod
    def giant_spider(cls) -> CharacterSheet:
        sheet = CharacterSheet()
        sheet.name = NPC._counter("Giant Spider")
        sheet.description = "Venomous Bite. 1d6+2."
        sheet.warrior_base = 6
        sheet.rogue_base = 6
        sheet.mage_base = 0
        sheet.armor = 4
        sheet.attack_attribute = SkillAttribute.Rogue
        wpn: Weapon = Weapon(name="Venomous Bite (Rogue)", base_damage="1d6x")
        wpn.damage_bonus = 2
        sheet.weapons.append(wpn)
        sheet.reset_pools()
        sheet.base_defense = 8
        sheet.hit_points_max = 24
        sheet.hp = 24  
        return jsonpickle.decode(jsonpickle.encode(sheet))


if __name__ == '__main__':
    print(NPC.giant_beetle().name)
