import copy

import jsonpickle

from character_sheet import CharacterSheet
from equipment import Weapon
from skills import CharacterSkillsList


class NPC:
    @classmethod
    def giant_beetle(cls) -> CharacterSheet:
        sheet = CharacterSheet()
        sheet.name = f"Giant Beetle"
        sheet.warrior = 4
        sheet.rogue = 4
        sheet.mage = 0
        sheet.defense = 5
        bite: Weapon = Weapon("Bite", CharacterSkillsList.skill_by_name("Unarmed"), "1d6", 0)
        sheet.weapons.append(bite)
        sheet.reset_pools()
        sheet.hit_points_max = 14
        sheet.hps = (14, 15)
        return sheet

    @classmethod
    def skeleton_warrior(cls) -> CharacterSheet:
        sheet = CharacterSheet()
        sheet.name = f"Skeleton Warrior"
        sheet.description = "Rusted armor. Broken shield. Short sword."
        sheet.warrior = 3
        sheet.rogue = 3
        sheet.mage = 0
        sheet.defense = 6
        sword: Weapon = copy.copy(Weapon.by_name("Sword"))
        sword.name = "Sword - Rusty"
        sheet.weapons.append(sword)
        sheet.reset_pools()
        sheet.hit_points_max = 9
        sheet.hps = (9, 5)
        return sheet

    @classmethod
    def skeleton_archer(cls) -> CharacterSheet:
        sheet = CharacterSheet()
        sheet.name = f"Skeleton Archer"
        sheet.description = "Rusted armor. Bow. 10 Arrows."
        sheet.warrior = 3
        sheet.rogue = 3
        sheet.mage = 0
        sheet.defense = 6
        wpn: Weapon = Weapon.by_name("Bow").copy()
        wpn.name = "Bow - Dry rotting"
        sheet.weapons.append(wpn)
        sheet.reset_pools()
        sheet.hit_points_max = 9
        sheet.hps = (9, 5)
        return sheet

    @classmethod
    def zombie(cls) -> CharacterSheet:
        sheet = CharacterSheet()
        sheet.name = f"Zombie"
        sheet.description = "Those bitten and killed by a zombie arise as zombies in 1d6 minutes each."
        sheet.warrior = 6
        sheet.rogue = 0
        sheet.mage = 0
        sheet.defense = 7
        wpn: Weapon = Weapon(name="Infected Bite", base_damage="1d6")
        sheet.weapons.append(wpn)
        sheet.reset_pools()
        sheet.hit_points_max = 12
        sheet.hps = (12, 0)
        return sheet

    @classmethod
    def giant_rat(cls) -> CharacterSheet:
        sheet = CharacterSheet()
        sheet.name = f"Giant Rat"
        sheet.description = "Bites. 1d6."
        sheet.warrior = 4
        sheet.rogue = 2
        sheet.mage = 0
        sheet.defense = 7
        wpn: Weapon = Weapon(name="Bite (Warrior)", base_damage="1d6")
        sheet.weapons.append(wpn)
        sheet.reset_pools()
        sheet.hit_points_max = 12
        sheet.hps = (12, 0)
        return jsonpickle.decode(jsonpickle.encode(sheet))


if __name__ == '__main__':
    print(NPC.giant_beetle().name)
