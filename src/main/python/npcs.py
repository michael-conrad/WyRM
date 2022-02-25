import copy

import jsonpickle

from character_sheet import CharacterSheet
from dnd5e_monsters import CharacterSheet5
from dnd5e_monsters import from_dnd5e
from equipment import Armor
from equipment import Weapon
from gb_utils import roll
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
        sheet.fate = 0
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
        sheet.equip_armor(Armor("Rusted chain mail", 1, 0, 0))
        sheet.fate = 0
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
        sheet.fate = 0
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
        sheet.fate = 0
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
        sheet.fate = 0
        return sheet

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
        sheet.fate = 0
        return sheet

    # Imprecise conversions from DnD 5e follow:

    @classmethod
    def awakened_shrub(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name =  NPC._counter("Awakened Shrub")
        dnd.armor_class = 9
        dnd.str = 3
        dnd.dex = 8
        dnd.con = 11
        dnd.int = 10
        dnd.wis = 10
        dnd.cha = 6
        dnd.xp = 10
        dnd.vulnerability = "Fire"
        dnd.resist = "Piercing"
        dnd.special = "While the shrub remains motionless, it is a normal shrub."
        dnd.weapon = "Rake with limbs"
        dnd.attack_bonus = 1
        dnd.damage = "1d4-1"
        dnd.desc = "An awakened shrub is an ordinary shrub given sentience and mobility by magic."

        branches: Weapon = Weapon("Rake with branches", base_damage="1d4x")
        branches.attack_bonus = 1
        branches.damage_bonus = -1
        dnd.weapon = branches

        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def giant_fire_beetle(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name= NPC._counter("Giant Fire Beetle")
        dnd.armor_class = 13
        dnd.str = 8
        dnd.dex = 10
        dnd.con = 12
        dnd.int = 1
        dnd.wis = 7
        dnd.cha = 3
        dnd.xp = 10
        dnd.attack_bonus = 1
        dnd.damage_bonus = -1
        dnd.damage = "1d6"
        dnd.desc = "A giant fire beetle is a nocturnal creature that features" \
                   " a pair of glowing glands that give off light for 1d6 days" \
                   " after the beetle dies."
        bite: Weapon = Weapon("Bite", base_damage="1d6x")
        bite.attack_bonus = 1
        bite.damage_bonus = -1
        dnd.weapon=bite

        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def blink_dog(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name =  NPC._counter("Blink Dog")
        dnd.armor_class = 13
        dnd.str = 12
        dnd.dex = 17
        dnd.con = 12
        dnd.int = 10
        dnd.wis = 13
        dnd.cha = 11
        dnd.xp = 50
        dnd.attack_bonus = 1
        dnd.damage_bonus = -1
        dnd.damage = "1d6"
        dnd.desc = "A blink dog takes its name from its ability to blink in" \
                   " and out of existence, a talent it uses to aid its attacks" \
                   " and to avoid harm."
        bite: Weapon = Weapon("Bite", base_damage="1d6x")
        bite.attack_bonus = 3
        bite.damage_bonus = 1
        dnd.weapon = bite

        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def giant_lizard(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name =  NPC._counter("Giant Lizard")
        dnd.armor_class = 12
        dnd.str = 15
        dnd.dex = 12
        dnd.con = 13
        dnd.int = 2
        dnd.wis = 10
        dnd.cha = 5
        dnd.xp = 50
        dnd.desc = "Giant lizards are fearsome predators often used as mounts" \
                   " or draft animals by reptilian humanoids and residents of" \
                   " the Underdark."
        bite: Weapon = Weapon("Bite", base_damage="1d8x")
        bite.attack_bonus = 4
        bite.damage_bonus = 2
        dnd.weapon = bite
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def giant_rat2(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name =  NPC._counter("Giant Rat")
        dnd.armor_class = 12
        dnd.str = 7
        dnd.dex = 15
        dnd.con = 11
        dnd.int = 2
        dnd.wis = 10
        dnd.cha = 4
        dnd.xp = 25
        dnd.desc = "Giant rat. Darkvision 60ft."
        bite: Weapon = Weapon("Bite", base_damage="1d4x")
        bite.attack_bonus = 4
        bite.damage_bonus = 2
        dnd.weapon = bite
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def giant_weasel(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name = NPC._counter("Giant Weasel")
        dnd.armor_class = 13
        dnd.str = 11
        dnd.dex = 16
        dnd.con = 10
        dnd.int = 4
        dnd.wis = 12
        dnd.cha = 5
        dnd.xp = 25
        dnd.desc = "Giant weasel."
        bite: Weapon = Weapon("Bite", base_damage="1d4x")
        bite.attack_bonus = 5
        bite.damage_bonus = 3
        dnd.weapon = bite
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def gnoll_warrior(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name = NPC._counter("Gnoll Warrior")
        dnd.armor_class = 15
        dnd.str = 14
        dnd.dex = 12
        dnd.con = 11
        dnd.int = 6
        dnd.wis = 10
        dnd.cha = 7
        dnd.xp = 100
        dnd.desc = "Gnoll warrior. Uses a spear."
        wpn: Weapon = Weapon("Spear", base_damage="1d6x")
        wpn.attack_bonus = 4
        wpn.damage_bonus = 2
        dnd.weapon = wpn
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def gnoll_archer(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name = NPC._counter("Gnoll Archer")
        dnd.armor_class = 15
        dnd.str = 14
        dnd.dex = 12
        dnd.con = 11
        dnd.int = 6
        dnd.wis = 10
        dnd.cha = 7
        dnd.xp = 100
        dnd.desc = "Gnoll archer."
        wpn: Weapon = Weapon("Longbow", base_damage="1d8x")
        wpn.attack_bonus = 3
        wpn.damage_bonus = 1
        dnd.weapon = wpn
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def goblin_warrior(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name = NPC._counter("Goblin Warrior")
        dnd.armor_class = 15
        dnd.str = 8
        dnd.dex = 14
        dnd.con = 10
        dnd.int = 10
        dnd.wis = 8
        dnd.cha = 8
        dnd.xp = 50
        dnd.desc = "Goblins are small, black-hearted humanoids that lair in despoiled dungeons and other dismal " \
                   "settings. Individually weak, they gather in large numbers to torment other creatures. "
        wpn: Weapon = Weapon("Scimitar", base_damage="1d6x")
        wpn.attack_bonus = 4
        wpn.damage_bonus = 2
        dnd.weapon = wpn
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def goblin_archer(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name = NPC._counter("Goblin Archer")
        dnd.armor_class = 15
        dnd.str = 8
        dnd.dex = 14
        dnd.con = 10
        dnd.int = 10
        dnd.wis = 8
        dnd.cha = 8
        dnd.xp = 50
        dnd.desc = "Goblins are small, black-hearted humanoids that lair in despoiled dungeons and other dismal " \
                   "settings. Individually weak, they gather in large numbers to torment other creatures. "
        wpn: Weapon = Weapon("Shortbow", base_damage="1d6x")
        wpn.attack_bonus = 4
        wpn.damage_bonus = 2
        dnd.weapon = wpn
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def hobgoblin_warrior(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name = NPC._counter("Hobgoblin Warrior")
        dnd.armor_class = 18
        dnd.str = 8
        dnd.dex = 14
        dnd.con = 10
        dnd.int = 10
        dnd.wis = 8
        dnd.cha = 8
        dnd.xp = 50
        dnd.desc = "Hobgoblins are large goblinoids with dark orange or red-orange skin. A hobgoblin measures virtue " \
                   "by physical strength and martial prowess, caring about nothing except skill and cunning in battle. "
        wpn: Weapon = Weapon("Longsword", base_damage="1d8x")
        wpn.attack_bonus = 3
        wpn.damage_bonus = 1
        dnd.weapon = wpn
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def hobgoblin_archer(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name = NPC._counter("Hobgoblin Archer")
        dnd.armor_class = 18
        dnd.str = 8
        dnd.dex = 14
        dnd.con = 10
        dnd.int = 10
        dnd.wis = 8
        dnd.cha = 8
        dnd.xp = 50
        dnd.desc = "Hobgoblins are large goblinoids with dark orange or red-orange skin. A hobgoblin measures virtue " \
                   "by physical strength and martial prowess, caring about nothing except skill and cunning in battle. "
        wpn: Weapon = Weapon("Longbow", base_damage="1d6x")
        wpn.attack_bonus = 3
        wpn.damage_bonus = 1
        dnd.weapon = wpn
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def kobold_warrior(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name = NPC._counter("Kobold Warrior")
        dnd.armor_class = 12
        dnd.str = 7
        dnd.dex = 15
        dnd.con = 9
        dnd.int = 8
        dnd.wis = 7
        dnd.cha = 8
        dnd.xp = 25
        dnd.desc = "Kobolds are craven reptilian humanoids that commonly infest dungeons. They make up for their " \
                   "physical ineptitude with a cleverness for trap making. "
        wpn: Weapon = Weapon("Dagger", base_damage="1d4x")
        wpn.attack_bonus = 4
        wpn.damage_bonus = 2
        dnd.weapon = wpn
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def skeleton_warrior2(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name = NPC._counter("Skeleton Warrior")
        dnd.armor_class = 13
        dnd.str = 10
        dnd.dex = 14
        dnd.con = 15
        dnd.int = 6
        dnd.wis = 8
        dnd.cha = 5
        dnd.xp = 50
        dnd.desc = ""
        wpn: Weapon = Weapon("Shortsword", base_damage="1d6x")
        wpn.attack_bonus = 4
        wpn.damage_bonus = 2
        dnd.weapon = wpn
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def skeleton_archer2(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name = NPC._counter("Skeleton Warrior")
        dnd.armor_class = 13
        dnd.str = 10
        dnd.dex = 14
        dnd.con = 15
        dnd.int = 6
        dnd.wis = 8
        dnd.cha = 5
        dnd.xp = 50
        dnd.desc = ""
        wpn: Weapon = Weapon("Shortbow", base_damage="1d6x")
        wpn.attack_bonus = 4
        wpn.damage_bonus = 2
        dnd.weapon = wpn
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def worg(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name = NPC._counter("Worg")
        dnd.armor_class = 13
        dnd.str = 16
        dnd.dex = 13
        dnd.con = 13
        dnd.int = 7
        dnd.wis = 11
        dnd.cha = 8
        dnd.xp = 100
        dnd.desc = "A worg is a monstrous wolf-like predator that delights in hunting and devouring creatures weaker " \
                   "than itself. "
        wpn: Weapon = Weapon("Bite", base_damage="2d6x")
        wpn.attack_bonus = 5
        wpn.damage_bonus = 3
        dnd.weapon = wpn
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def zombie2(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name = NPC._counter("Zombie")
        dnd.armor_class = 8
        dnd.str = 13
        dnd.dex = 6
        dnd.con = 16
        dnd.int = 3
        dnd.wis = 6
        dnd.cha = 5
        dnd.xp = 50
        dnd.desc = "Undead zombies move with a jerky, uneven gait. They are clad in the moldering apparel they wore " \
                   "when put to rest, and carry the stench of decay. "
        wpn: Weapon = Weapon("Slam", base_damage="1d6x")
        wpn.attack_bonus = 3
        wpn.damage_bonus = 1
        dnd.weapon = wpn
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def earth_elemental(cls) -> CharacterSheet:
        dnd = CharacterSheet5()
        dnd.name = NPC._counter("Earth Elemental")
        dnd.armor_class = 17
        dnd.hp = 126
        dnd.str = 20
        dnd.dex = 8
        dnd.con = 20
        dnd.int = 5
        dnd.wis = 10
        dnd.cha = 5
        dnd.xp = 1800
        dnd.desc = "An earth elemental plods forward like a walking hill, club-like arms of jagged stone swinging at " \
                   "its sides. Its head and body consist of dirt and stone, occasionally set with chunks of metal, " \
                   "gems, and bright minerals. "
        wpn: Weapon = Weapon("Slam", base_damage="2d8")
        wpn.attack_bonus = 8
        wpn.damage_bonus = 5
        dnd.weapon = wpn
        sheet = from_dnd5e(dnd)
        return sheet


if __name__ == '__main__':
    print(NPC.giant_beetle().name)
