import copy
import random
import types

from character_sheet import CharacterSheet
from dnd5e_monsters import CharacterSheet5
from dnd5e_monsters import from_dnd5e
from equipment import Armor
from equipment import Weapon
from gamebook_core import dice_roll
from skills import CharacterSkillsList
from skills import SkillAttribute

_npc_section_tag: str | None = ""


def npc_section_tag(tag: str) -> str:
    global _npc_section_tag
    _npc_section_tag = tag
    return _npc_section_tag


class NPC:
    _counter_: dict[str, int] = dict()

    @classmethod
    def spawn(cls, creature: types.FunctionType, count: int = 1) -> list[CharacterSheet]:
        count = max(0, count)
        result: list[CharacterSheet] = list()
        for _ in range(count):
            result.append(creature())
        return result

    @classmethod
    @property
    def section_tag(cls) -> str:
        global _npc_section_tag
        return _npc_section_tag

    @classmethod
    def set_section_tag(cls, tag: str | None) -> None:
        global _npc_section_tag
        _npc_section_tag = tag

    @classmethod
    def _counter(cls, name: str) -> str:
        # global _npc_section_tag
        # if _npc_section_tag and _npc_section_tag.lower() not in name.lower():
        #     name += f" {_npc_section_tag}"
        # if name not in cls._counter_:
        #     cls._counter_[name] = 0
        # cls._counter_[name] = cls._counter_[name] + 1
        # return f"{name} (#{cls._counter_[name]})"
        return f"{name}"

    @classmethod
    def giant_beetle(cls, extra_name: str | None = None) -> CharacterSheet:
        sheet = CharacterSheet()
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        sheet.name = NPC._counter(f"Giant Beetle{extra_name}")
        sheet.warrior_base = 4
        sheet.rogue_base = 4
        sheet.mage_base = 0
        sheet.armor_class = 3
        bite: Weapon = Weapon("Bite", CharacterSkillsList.skill_by_name("Unarmed"), "1d6", 0)
        sheet.weapons.append(bite)
        sheet.reset_pools()
        sheet.base_defense = 8 - sheet.armor_class
        sheet.hit_points_max = 2*6+2
        sheet.hp = dice_roll(2, 6)+2
        sheet.fate = 0
        return sheet

    @classmethod
    def skeleton_warrior(cls, extra_name: str | None = None) -> CharacterSheet:
        sheet = CharacterSheet()
        if extra_name is None:
            sheet.name = NPC._counter("Skeleton Warrior")
        else:
            sheet.name = NPC._counter(f"Skeleton Warrior {extra_name}")
        sheet.description = "Rusted armor. Broken shield. Short sword."
        sheet.warrior_base = 3
        sheet.rogue_base = 3
        sheet.mage_base = 0
        sheet.armor_class = 1
        sword: Weapon = copy.copy(Weapon.by_name("Sword"))
        sword.name = "Sword - Rusty"
        sheet.weapons.append(sword)
        sheet.reset_pools()
        sheet.base_defense = 7 - sheet.armor_class
        sheet.hit_points_max =2*8+4
        sheet.hp = dice_roll(2,8) + 4
        sheet.equip_armor(Armor("Rusted chain mail", 1, 0, 0))
        sheet.fate = 0
        return sheet

    @classmethod
    def skeleton_archer(cls, extra_name: str | None = None) -> CharacterSheet:
        sheet = CharacterSheet()
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        sheet.name = NPC._counter(f"Skeleton Archer{extra_name}")
        sheet.description = "Rusted armor. Bow. 10 Arrows."
        sheet.warrior_base = 3
        sheet.rogue_base = 3
        sheet.mage_base = 0
        sheet.armor_class = 1
        wpn: Weapon = Weapon.by_name("Bow")
        wpn.name = "Bow - Dry rotting"
        sheet.weapons.append(wpn)
        sheet.reset_pools()
        sheet.base_defense = 7 - sheet.armor_class
        sheet.hit_points_max = 2*8+4
        sheet.hp = dice_roll(2, 8) + 4
        sheet.fate = 0
        return sheet

    @classmethod
    def zombie(cls, extra_name: str | None = None) -> CharacterSheet:
        sheet = CharacterSheet()
        if extra_name is None:
            sheet.name = NPC._counter("Zombie")
        else:
            sheet.name = NPC._counter(f"Zombie {extra_name}")
        sheet.description = "Those bitten and killed by a zombie arise as zombies in 1d6 minutes each."
        sheet.warrior_base = 6
        sheet.rogue_base = 0
        sheet.mage_base = 0
        sheet.armor_class = 0
        wpn: Weapon = Weapon(name="Infected Bite", base_damage="1d6x")
        sheet.weapons.append(wpn)
        sheet.reset_pools()
        sheet.base_defense = 7
        sheet.hit_points_max = 3*8 + 9
        sheet.hp = dice_roll(3, 8) +9
        sheet.fate = 0
        return sheet

    @classmethod
    def giant_rat(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        sheet = CharacterSheet()
        sheet.name = NPC._counter(f"Giant Rat{extra_name}")
        sheet.description = "Bites. 1d6."
        sheet.warrior_base = 4
        sheet.rogue_base = 2
        sheet.mage_base = 0
        sheet.armor_class = 0
        wpn: Weapon = Weapon(name="Bite (Warrior)", base_damage="1d6x")
        sheet.weapons.append(wpn)
        sheet.reset_pools()
        sheet.base_defense = 7
        sheet.hit_points_max = 2*6
        sheet.hp = dice_roll(2, 6)
        sheet.fate = 0
        return sheet

    @classmethod
    def giant_spider(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        sheet = CharacterSheet()
        sheet.name = NPC._counter(f"Giant Spider{extra_name}")
        sheet.description = "!spider_parts=['head'," \
                            " 'thorax', 'legs', 'Pedipalps', 'Eyes', 'Abdomen'," \
                            " 'Spinnerets', 'Lungs', 'Fangs', 'Mouth', 'Sternum']"
        sheet.warrior_base = 6
        sheet.rogue_base = 6
        sheet.mage_base = 0
        sheet.armor_class = 4
        sheet.attack_attribute = SkillAttribute.Rogue
        wpn: Weapon = Weapon(name="Venomous Bite (Rogue)", base_damage="1d6x")
        wpn.damage_bonus = 2
        sheet.weapons.append(wpn)
        sheet.reset_pools()
        sheet.base_defense = 8
        sheet.hit_points_max = 4*10+4
        sheet.hp = dice_roll(4,10)+4
        sheet.fate = 0
        return sheet

    # Imprecise conversions from DnD 5e follow:

    @classmethod
    def awakened_shrub(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Awakened Shrub{extra_name}")
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
        dnd.hp = (3, 6, 0)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def giant_fire_beetle(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Giant Fire Beetle {extra_name}")
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
        dnd.weapon = bite
        dnd.hp = (1, 6, 1)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def blink_dog(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Blink Dog{extra_name}")
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
        dnd.hp = (4, 8, 4)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def giant_lizard(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Giant Lizard{extra_name}")
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
        dnd.hp = (3, 10, 3)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def giant_rat2(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Giant Rat{extra_name}")
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
        dnd.hp = (2, 6, 0)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def giant_weasel(cls, extra_name: str | None = None) -> CharacterSheet:
        dnd = CharacterSheet5()
        if extra_name is None:
            dnd.name = NPC._counter("Giant Weasel")
        else:
            dnd.name = NPC._counter(f"Giant Weasel {extra_name}")
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
        dnd.hp = (2, 8, 0)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def gnoll_warrior(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Gnoll Warrior{extra_name}")
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
        dnd.hp = (5, 8, 0)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def gnoll_archer(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Gnoll Archer{extra_name}")
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
        dnd.hp = (5, 8, 0)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def goblin_warrior(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Goblin Warrior{extra_name}")
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
        dnd.hp = (2, 6, 0)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def goblin_archer(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Goblin Archer{extra_name}")
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
        dnd.hp = (2, 6, )
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def hobgoblin_warrior(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Hobgoblin Warrior{extra_name}")
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
        dnd.hp = (2, 8, 2)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def hobgoblin_archer(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Hobgoblin Archer{extra_name}")
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
        dnd.hp = (2, 8, 2)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def kobold_warrior(cls, extra_name: str | None = None) -> CharacterSheet:
        dnd = CharacterSheet5()
        if extra_name is None:
            dnd.name = NPC._counter("Kobold Warrior")
        else:
            dnd.name = NPC._counter(f"Kobold Warrior {extra_name}")
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
        dnd.hp = (2, 6, -2)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def skeleton_warrior2(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Skeleton Warrior{extra_name}")
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
        dnd.hp = (2, 8, 4)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def skeleton_archer2(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Skeleton Warrior{extra_name}")
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
        dnd.hp = (2, 8, 4)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def worg(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Worg{extra_name}")
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
        dnd.hp = (4, 10, 4)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def zombie2(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Zombie{extra_name}")
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
        dnd.hp = (3, 8, 9)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def earth_elemental(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Earth Elemental{extra_name}")
        dnd.armor_class = 17
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
        dnd.hp = (12, 10, 60)
        sheet = from_dnd5e(dnd)
        return sheet

    @classmethod
    def shadow(cls, extra_name: str | None = None) -> CharacterSheet:
        if extra_name is None:
            extra_name = ""
        else:
            extra_name = f" {extra_name.strip()}"
        dnd = CharacterSheet5()
        dnd.name = NPC._counter(f"Shadow{extra_name}")
        dnd.armor_class = 12
        dnd.str = 6
        dnd.dex = 14
        dnd.con = 13
        dnd.int = 6
        dnd.wis = 10
        dnd.cha = 8
        dnd.xp = 100
        dnd.desc = "Shadows are undead that resemble dark exaggerations of humanoid shadows."
        wpn: Weapon = Weapon("Life Drain", base_damage="2d6+2")
        wpn.attack_bonus = 4
        wpn.damage_bonus = 0
        dnd.weapon = wpn
        dnd.hp = (3, 8, 3)
        sheet = from_dnd5e(dnd)
        return sheet


def wander(pct: int = 10) -> bool:
    if random.randint(0, 99) <= pct:
        return True
    return False


def wander_monsters(die_count: int = 1) -> list[CharacterSheet]:
    choices: list[list[CharacterSheet]] = list()
    d2: int = dice_roll(die_count, 2) - (die_count-1)
    d3: int = dice_roll(die_count, 3) - (die_count-1)
    d4: int = dice_roll(die_count, 4) - (die_count-1)
    d6: int = dice_roll(die_count, 6) - (die_count-1)
    d8: int = dice_roll(die_count, 8) - (die_count-1)
    d10: int = dice_roll(die_count, 10) - (die_count-1)

    i: list[CharacterSheet]

    i = list()
    for _ in range(d3):
        i.append(NPC.skeleton_warrior())
    choices.append(i)

    i = list()
    for _ in range(d2):
        i.append(NPC.zombie())
    choices.append(i)

    i = list()
    for _ in range(d3):
        i.append(NPC.giant_rat())
    choices.append(i)

    i = list()
    for _ in range(d2):
        i.append(NPC.giant_spider())
    choices.append(i)

    i = list()
    for _ in range(d10):
        i.append(NPC.awakened_shrub())
    choices.append(i)

    i = list()
    for _ in range(d2):
        i.append(NPC.giant_lizard())
    choices.append(i)

    i = list()
    for _ in range(d4):
        i.append(NPC.giant_weasel())
    choices.append(i)

    i = list()
    for _ in range(d2):
        i.append(NPC.goblin_warrior())
    choices.append(i)

    i = list()
    for _ in range(d3):
        i.append(NPC.hobgoblin_warrior())
    choices.append(i)

    i = list()
    for _ in range(d4):
        i.append(NPC.kobold_warrior())
    choices.append(i)

    i = list()
    for _ in range(d2):
        i.append(NPC.worg())
    choices.append(i)

    m = random.choice(choices)
    return random.choice(choices)


if __name__ == '__main__':
    print(NPC.giant_beetle().name)

