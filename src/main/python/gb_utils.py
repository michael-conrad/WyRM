import random

import dice
import jsonpickle

import character_sheet
from equipment import Armor
from equipment import Item
from equipment import Money
from equipment import Shield
from equipment import Weapon
from gamebook_core import dice_roll
from skills import Difficulty


def get_loot(challenge: int) -> list[Item | Weapon | Armor | Shield | Money | str]:
    result: list[Item | Weapon | Armor | Shield | Money | str] = list()

    cp: int = 0
    sp: int = 0
    ep: int = 0
    gp: int = 0
    pp: int = 0

    d100: int = dice_roll(1, 100)
    if challenge < 5:
        # challenge 0-4 table
        if d100 <= 30:
            cp += dice_roll(5, 6)
        elif d100 <= 60:
            sp += dice_roll(4, 6)
        elif d100 <= 70:
            ep += dice_roll(3, 6)
        elif d100 <= 95:
            gp += dice_roll(3, 6)
        else:
            pp += dice_roll(1, 6)
    elif challenge < 11:
        # challenge 5-10 table
        if d100 <= 30:
            cp += dice_roll(4, 6) * 100
            ep += dice_roll(1, 6) * 10
        elif d100 <= 60:
            sp += dice_roll(6, 6) * 10
            gp += dice_roll(2, 6) * 10
        elif d100 <= 70:
            ep += dice_roll(3, 6) * 10
            gp += dice_roll(4, 6) * 10
        elif d100 <= 95:
            gp += dice_roll(5, 6) * 10
        else:
            gp += dice_roll(2, 6) * 10
            pp += dice_roll(3, 6)
    elif challenge < 17:
        if d100 <= 20:
            sp += dice_roll(4, 6) * 100
            gp += dice_roll(1, 6) * 100
        elif d100 <= 35:
            ep += dice_roll(1, 6) * 100
            gp += dice_roll(1, 6) * 100
        elif d100 <= 75:
            gp += dice_roll(2, 6) * 100
            pp += dice_roll(1, 6) * 10
        else:
            gp += dice_roll(2, 6) * 100
            pp += dice_roll(2, 6) * 10
    else:
        if d100 <= 15:
            ep += dice_roll(2, 6) * 1000
            gp += dice_roll(8, 6) * 100
        elif d100 <= 55:
            gp += dice_roll(1, 6) * 1000
            pp += dice_roll(1, 6) * 100
        else:
            gp += dice_roll(1, 6) * 100
            pp += dice_roll(2, 6) * 100

    if cp:
        result.append(Money("CP", cp))
    if sp:
        result.append(Money("SP", sp))
    if ep:
        result.append(Money("EP", ep))
    if gp:
        result.append(Money("GP", gp))
    if pp:
        result.append(Money("PP", pp))

    return result


def debug(thing: any) -> str:
    s: str = str(thing)
    print(f"DEBUG: {s}")
    return s


def unpickle(pickled: str) -> any:
    return jsonpickle.decode(pickled)


def pickle(o: any) -> str:
    return jsonpickle.encode(o)


def deepcopy(o: any) -> any:
    if o is None:
        return None
    return jsonpickle.decode(jsonpickle.encode(o))


def roll(die: str) -> int:
    if die.strip()[-1] != "t":
        die += " t"
    return max(0, int(dice.roll(f"{die}")))


def dark_power_intervention_text() -> str:
    return """
   
You can't move. Before you appears a two-handed axe dripping with blood and a voice booms out:

"Ah! Entertainment! Agree to do a task for me and have a chance to live. Refuse and you most certainly will die. 
There is an amulet secreted away on a shadow plane where locations from this reality show up in that reality. 
Retrieving this amulet then escaping the complex will result in your life being spared. After obtaining the amulet, 
take it to a place of my choosing for a reward beyond just your life." 

:Accept task
:Refuse task
"""


def intervention(check: int | None = None) -> str:
    check = dice_roll(3, 6) if check is None else check
    "3,4, 5,6, 7,8, 9,10, 11,12, 13,14, 15,16, 17,18"
    if check <= 4:
        return f"""
; Dark Power Intervention ({check}).
{dark_power_intervention_text()}
"""
    if check <= 6:
        effect: str = random.choice(
                ["Hidden floor pit full of spikes triggers. (3d6 dmg).", "Spontaneous Combustion. (2d8 dmg).",
                 "Hidden darts trap from wall triggers. (3d4 dmg).",
                 "Hidden spikes trap from ceiling triggers. (3d8 dmg)"])
        return f"{effect} ({check})."
    if check <= 8:
        creatures: str = random.choice(
                ["Bears", "Large Cats", "Fire Beetles", "Giant Beetles", "Giant Rats", "Giant Spiders", "Dire Wolves",
                 "Earth Elementals", "War Golems", "Warrior Skeletons", "Archer Skeletons", "Zombies"])
        return f"{roll('1d4+1')} {creatures} show up and attacks opponent(s)." \
               f" Player gets an automatic flee success check. " \
               f" Creatures will attack player if they run out of opponents." \
               f" ({check})"
    if check <= 10:
        creatures: str = random.choice(
                ["Goblins", "Kobolds", "Hobgoblins", "Worgs", "Gnolls", "Giant Weasals", "Giant Lizards",
                 "Awakened Shrubs"])
        return f"{roll('1d4+1')} {creatures} show up and attacks opponent(s)." \
               f" Player gets an automatic flee success check. " \
               f" Creatures will attack player if they run out of opponents." \
               f" ({check})"
    if check <= 12:
        return f"Opposing forces make a mistake, trip up, get in the way of each other" \
               f" Player gets an automatic flee success check. " \
               f" Opponents will attack player next round.  ({check})."
    if check <= 14:
        return f"Opposing forces attack each other or hurt themselves with own weapons." \
               f" Player gets an automatic flee success check. " \
               f" Opponents will attack player next round.  ({check})."
    if check <= 16:
        trap: str = random.choice(["Magical Scythe Blades appear then vanish. 4d10 dmg.",
                                   "Thunderstone Mine. A mine under the floor is triggered. 4d10 dmg.",
                                   "Huge falling block. 10 ft area. 4d10 dmg."])
        return f"{trap} ({check})"
    return f"Divine Intervention ({check})."


def dark_god() -> str:
    gods: list[str] = list()
    gods.append("Blibdoolpoolp, kuo-toa goddess, [NE], Death, Lobster head or black perl.")
    gods.append("Laogzed, troglodyte god of hunger, [CE], Death, Image of lizard/toad")
    gods.append("Grolantor, hill giant god of war, [CE], War, Wooden Club")
    gods.append("Hruggek, bugbear god of violence, [CE], War, Morningstar")
    gods.append("Kurtulmak, kobold god of war and mining, [LE], War, Gnome skull")
    gods.append("Maglubiyet, goblinoid god of war, [LE], War, Bloody axe")
    gods.append("Thrym, god of frost giants and strength, [CE], War, White double-bladed axe")
    return random.choice(gods)


def divine_god() -> str:
    gods: list[str] = list()
    gods.append("Blibdoolpoolp, kuo-toa goddess, [NE], Death, Lobster head or black perl.")
    gods.append("Laogzed, troglodyte god of hunger, [CE], Death, Image of lizard/toad")
    gods.append("Grolantor, hill giant god of war, [CE], War, Wooden Club")
    gods.append("Hruggek, bugbear god of violence, [CE], War, Morningstar")
    gods.append("Kurtulmak, kobold god of war and mining, [LE], War, Gnome skull")
    gods.append("Maglubiyet, goblinoid god of war, [LE], War, Bloody axe")
    gods.append("Thrym, god of frost giants and strength, [CE], War, White double-bladed axe")
    return random.choice(gods)


def list_chars(state: dict) -> str:
    char_list: str = ""
    for key in state:
        var = state[key]
        if isinstance(var, type):
            continue
        if hasattr(var, "hp") and hasattr(var, "name"):
            if getattr(var, "hp"):
                char_list += f"\n;## {key}: {var.name}"
            else:
                char_list += f"\n;## {key}: {var.name} (DEAD)"
    return char_list


def delete_dead_chars(state: dict) -> str:
    char_list: str = ""
    to_delete: list[str] = list()
    for key in state:
        var = state[key]
        if isinstance(var, type):
            continue
        if hasattr(var, "hp") and hasattr(var, "name"):
            if getattr(var, "hp"):
                char_list += f"\n;## {key}: {var.name}"
            else:
                char_list += f"\n;## {key}: {var.name} (DEAD)"
                to_delete.append(key)
    if to_delete:
        for key in to_delete:
            del state[key]
    return char_list


def list_items(state: dict) -> str:
    item_list: str = ""
    for key in state:
        var = state[key]
        if isinstance(var, type):
            continue
        if isinstance(var, Item) or isinstance(var, Weapon) or isinstance(var, Armor) or isinstance(var, Shield):
            item_list += f"\n;##  {key}: {var.name}"
    return item_list


def dl_check(difficulty_name: str, attribute_value: int) -> str:
    _: str = ""
    for difficulty in Difficulty:
        if difficulty.name.lower() == difficulty_name.lower():
            die_value: int = roll("1d6x")
            check: int = die_value + attribute_value
            return f"PASS {check} >= {difficulty.value}" if check >= difficulty.value \
                else f"FAIL {check} < {difficulty.value}"
        _ += f"{difficulty.name} ({difficulty.value}); "
    return f"{difficulty_name} unknown. {_}"


def stat_check(stat: int, bonus: int) -> bool:
    check: int = roll(f"1d6x + {bonus}")
    return check >= stat


def initiative(side_a=None,  #
               side_b=None) -> str:
    side_a: int | character_sheet.CharacterSheet | list[character_sheet.CharacterSheet] | None
    side_b: int | character_sheet.CharacterSheet | list[character_sheet.CharacterSheet] | None
    name1: str = "First Group"
    name2: str = "Second Group"
    if isinstance(side_a, list):
        _: character_sheet.CharacterSheet | None = None
        for p in side_a:
            if p.is_alive:
                _ = p
                break
        side_a = _
    if isinstance(side_b, list):
        _: character_sheet.CharacterSheet | None = None
        for p in side_b:
            if p.is_alive:
                _ = p
                break
        side_b = _
    if isinstance(side_a, character_sheet.CharacterSheet):
        name1 = side_a.name
        side_a = side_a.rogue
    if isinstance(side_b, character_sheet.CharacterSheet):
        name2 = side_b.name
        side_b = side_b.rogue
    if side_a is None:
        side_a = 0
    if side_b is None:
        side_b = 0
    roll1: int = roll(f"1d6+{side_a}")
    roll2: int = roll(f"1d6+{side_b}")
    if roll1 > roll2:
        return f"First Group: {name1}"
    if roll1 < roll2:
        return f"Second Group: {name2}"
    return initiative(side_a, side_b)


def initiative_check(side_a: int = 0, side_b: int = 0) -> bool:
    if side_a is None:
        side_a = 0
    if side_b is None:
        side_b = 0
    if type(side_a).__name__ == "MobUnit":
        side_a = side_a.rogue
    if type(side_a).__name__ == "MobUnit":
        side_b = side_b.rogue
    if isinstance(side_a, list):
        side_a = side_a[0].rogue
    if isinstance(side_b, list):
        side_b = side_b[0].rogue
    if isinstance(side_a, character_sheet.CharacterSheet):
        side_a = side_a.rogue
    if isinstance(side_b, character_sheet.CharacterSheet):
        side_b = side_b.rogue

    roll1: int = roll(f"1d6+{side_a}")
    roll2: int = roll(f"1d6+{side_b}")
    if roll1 > roll2:
        return True
    if roll1 < roll2:
        return False
    return initiative_check(side_a, side_b)


def loot_box(qty: int = 1, seed: int | None = None) -> list[str]:
    if seed is not None:
        r = random.Random(seed)
    else:
        r = random.Random()
    items: list[str] = list()
    while len(items) < qty:
        item: str = "; " + loot(r)
        if item in items:
            continue
        items.append(item)
    items.sort()
    return items


def loot(r: random.Random | None = None) -> str:
    if r is None:
        r = random.Random()
    items: list[str] = list()
    if r.randint(1, 100) < 75:
        bns = r.randint(1, 3)
        items.append(f"Amulet of Health, Max HP: {bns:+}")
        bns = r.randint(1, 3)
        items.append(f"Belt of Might, Warrior: {bns:+}")
        d100 = r.randint(1, 100)
        bns = 1 if d100 < 75 else 2 if d100 < 96 else 3
        d6 = r.randint(1, 6)
        if d6 < 5:
            _ = r.randint(1, 6)
            if _ <= 2:
                items.append(f"Small Shield {bns:+}")
            elif _ <= 5:
                items.append(f"Large Shield {bns:+}")
            else:
                items.append(f"Tower Shield {bns:+}")
        else:
            _ = r.randint(1, 6)
            if _ == 1:
                items.append(f"Leather armor {bns:+}")
            elif _ == 2:
                items.append(f"Scale mail armor {bns:+}")
            elif _ == 3:
                items.append(f"Lamellar mail armor {bns:+}")
            elif _ == 4:
                items.append(f"Chain mail armor {bns:+}")
            elif _ == 5:
                items.append(f"Light plate mail armor {bns:+}")
            else:
                items.append(f"Heavy plate mail armor {bns:+}")

        items.append("Bag of Holding")
        bns = r.randint(1, 3)
        items.append(f"Boots of Striding and Springing, Rogue: {bns:+}")
        bns = r.randint(1, 3)
        items.append(f"Cloak of Elvenkind, Mage: {bns:+}, Rogue: {bns:+}")
        bns = r.randint(1, 3)
        items.append(f"Gauntlets of Ogre Power, Warrior {bns:+}")
        items.append("Gloves of Swimming and Climbing")
        items.append("Goggles of Night (darkvision 60ft)")
        bns = r.randint(1, 3)
        items.append(f"Headband of Intellect, Mage: {bns:+}")
        bns = r.randint(1, 4) + 1
        items.append(f"Keoghtom's Ointment, doses: {bns}, heals 2d8+2")
        items.append("Potion of Flying")
        items.append("Potion of Invisibility")
        points = r.randint(1, 8) + r.randint(1, 8) + r.randint(1, 8)
        items.append(f"Potion of Vitality ({points:+})")
        items.append(f"Potion of Mana Restoration ({points:+})")
        bns = r.randint(1, 3)
        items.append(f"Ring of Evasion, Rogue: {bns:+}")
        items.append("Ring of Protection, BASE ARMOR +1")
        items.append("Ring of Resistance, 1d10: see pg60 DMBasicRulesv.0.3")
        d100 = r.randint(1, 100)
        circle = 1 if d100 < 56 else 2 if d100 < 81 else 3 if d100 < 94 else 4
        items.append(f"Spell Scroll: Circle {circle} ")
        items.append("Wand of Magic Detection, 1d3 uses/day")
        items.append("Wand of Magic Missiles, 1d3 uses/day")
        d100 = r.randint(1, 100)
        bns = 1 if d100 < 75 else 2 if d100 < 96 else 3
        d6 = r.randint(1, 6)
        if d6 <= 3:
            # Bladed
            _ = r.randint(1, 6)
            if _ <= 4:
                items.append(f"Sword {bns:+}")
            elif _ == 5:
                items.append(f"Dagger {bns:+}")
            else:
                items.append(f"Two-Handed Sword {bns:+}")
        elif d6 == 4:
            # Bludgeon
            _ = r.randint(1, 6)
            if _ <= 3:
                items.append(f"Warhammer {bns:+}")
            elif _ <= 5:
                items.append(f"Mace {bns:+}")
            else:
                items.append(f"Two-handed Warhammer {bns:+}")
                items.append(f"Two-handed Mace {bns:+}")
        elif d6 == 5:
            # Bow
            _ = r.randint(1, 6)
            if _ <= 4:
                items.append(f"Short bow {bns:+}")
            else:
                items.append(f"Long bow {bns:+}")
        else:
            # Other
            _ = r.randint(1, 6)
            if _ <= 2:
                items.append(f"Axe {bns:+}")
            elif _ <= 5:
                items.append(f"Spear {bns:+}")
            else:
                items.append(f"Two-handed axe {bns:+}")
    else:
        bns = - r.randint(1, 3)
        items.append(f"Amulet of Weakness, Max HP: {bns:+}")
        d100 = r.randint(1, 100)
        bns = -1 if d100 < 75 else -2 if d100 < 96 else -3
        d6 = r.randint(1, 6)
        if d6 < 5:
            _ = r.randint(1, 6)
            if _ <= 2:
                items.append(f"Small Shield {bns:+}")
            elif _ <= 5:
                items.append(f"Large Shield {bns:+}")
            else:
                items.append(f"Tower Shield {bns:+}")
        else:
            _ = r.randint(1, 6)
            if _ == 1:
                items.append(f"Leather armor {bns:+}")
            elif _ == 2:
                items.append(f"Scale mail armor {bns:+}")
            elif _ == 3:
                items.append(f"Lamellar mail armor {bns:+}")
            elif _ == 4:
                items.append(f"Chain mail armor {bns:+}")
            elif _ == 5:
                items.append(f"Light plate mail armor {bns:+}")
            else:
                items.append(f"Heavy plate mail armor {bns:+}")
        items.append("Bag of Devouring")
        bns = - r.randint(1, 3)
        items.append(f"Boots of Clumsiness, Rogue: {bns:+}")
        bns = - r.randint(1, 3)
        items.append(f"Gauntlets of Sapping Strength, Warrior: {bns:+}")
        bns = - r.randint(1, 3)
        items.append(f"Headband of Dull Thinking, Mage: {bns:+}")
        bns = - r.randint(1, 4) + 1
        items.append(f"Keoghtaz's Ointment, doses: {bns}, damages 2d8+2")
        bns = - (r.randint(1, 4) + r.randint(1, 4))
        items.append(f"Potion of Health Drain. HP: {bns:+}")
        items.append(f"Potion of Mana Drain. Mana: ({bns:+})")
        bns = - r.randint(1, 3)
        items.append(f"Ring of Clumsiness, Rogue: {bns:+}")
        items.append("Ring of Slowness, Rogue: -1")
        d100 = r.randint(1, 100)
        bns = -1 if d100 < 75 else -2 if d100 < 96 else -3
        if d6 <= 3:
            # Bladed
            _ = r.randint(1, 6)
            if _ <= 4:
                items.append(f"Sword {bns:+}")
            elif _ == 5:
                items.append(f"Dagger {bns:+}")
            else:
                items.append(f"Two-Handed Sword {bns:+}")
        elif d6 == 4:
            # Bludgeon
            _ = r.randint(1, 6)
            if _ <= 3:
                items.append(f"Warhammer {bns:+}")
            elif _ <= 5:
                items.append(f"Mace {bns:+}")
            else:
                items.append(f"Two-handed Warhammer {bns:+}")
                items.append(f"Two-handed Mace {bns:+}")
        elif d6 == 5:
            # Bow
            _ = r.randint(1, 6)
            if _ <= 4:
                items.append(f"Short bow {bns:+}")
            else:
                items.append(f"Long bow {bns:+}")
        else:
            # Other
            _ = r.randint(1, 6)
            if _ <= 2:
                items.append(f"Axe {bns:+}")
            elif _ <= 5:
                items.append(f"Spear {bns:+}")
            else:
                items.append(f"Two-handed axe {bns:+}")
    return r.choice(items)


def loot_armor_weapon(r: random.Random | None = None) -> str:
    if r is None:
        r = random.Random()
    items: list[str] = list()
    if r.randint(1, 100) < 75:
        bns = r.randint(1, 3)
        items.append(f"Belt of Might, Warrior: {bns:+}")
        d100 = r.randint(1, 100)
        bns = 1 if d100 < 75 else 2 if d100 < 96 else 3
        d6 = r.randint(1, 6)
        if d6 < 5:
            _ = r.randint(1, 6)
            if _ <= 2:
                items.append(f"Small Shield {bns:+}")
            elif _ <= 5:
                items.append(f"Large Shield {bns:+}")
            else:
                items.append(f"Tower Shield {bns:+}")
        else:
            _ = r.randint(1, 6)
            if _ == 1:
                items.append(f"Leather armor {bns:+}")
            elif _ == 2:
                items.append(f"Scale mail armor {bns:+}")
            elif _ == 3:
                items.append(f"Lamellar mail armor {bns:+}")
            elif _ == 4:
                items.append(f"Chain mail armor {bns:+}")
            elif _ == 5:
                items.append(f"Light plate mail armor {bns:+}")
            else:
                items.append(f"Heavy plate mail armor {bns:+}")

        items.append(f"Boots of Striding and Springing, Rogue: {bns:+}")
        bns = r.randint(1, 3)
        items.append(f"Cloak of Elvenkind, Mage: {bns:+}, Rogue: {bns:+}")
        bns = r.randint(1, 3)
        items.append(f"Gauntlets of Ogre Power, Warrior {bns:+}")
        bns = r.randint(1, 3)
        items.append(f"Ring of Evasion, Rogue: {bns:+}")
        bns = r.randint(1, 3)
        items.append(f"Ring of Protection, Defense {bns:+}")
        d100 = r.randint(1, 100)
        bns = 1 if d100 < 75 else 2 if d100 < 96 else 3
        d6 = r.randint(1, 6)
        if d6 <= 3:
            # Bladed
            _ = r.randint(1, 6)
            if _ <= 4:
                items.append(f"Sword {bns:+}")
            elif _ == 5:
                items.append(f"Dagger {bns:+}")
            else:
                items.append(f"Two-Handed Sword {bns:+}")
        elif d6 == 4:
            # Bludgeon
            _ = r.randint(1, 6)
            if _ <= 3:
                items.append(f"Warhammer {bns:+}")
            elif _ <= 5:
                items.append(f"Mace {bns:+}")
            else:
                items.append(f"Two-handed Warhammer {bns:+}")
                items.append(f"Two-handed Mace {bns:+}")
        elif d6 == 5:
            # Bow
            _ = r.randint(1, 6)
            if _ <= 4:
                items.append(f"Short bow {bns:+}")
            else:
                items.append(f"Long bow {bns:+}")
        else:
            # Other
            _ = r.randint(1, 6)
            if _ <= 2:
                items.append(f"Axe {bns:+}")
            elif _ <= 5:
                items.append(f"Spear {bns:+}")
            else:
                items.append(f"Two-handed axe {bns:+}")
    else:
        d100 = r.randint(1, 100)
        bns = -1 if d100 < 75 else -2 if d100 < 96 else -3
        d6 = r.randint(1, 6)
        if d6 < 5:
            _ = r.randint(1, 6)
            if _ <= 2:
                items.append(f"Small Shield {bns:+}")
            elif _ <= 5:
                items.append(f"Large Shield {bns:+}")
            else:
                items.append(f"Tower Shield {bns:+}")
        else:
            _ = r.randint(1, 6)
            if _ == 1:
                items.append(f"Leather armor {bns:+}")
            elif _ == 2:
                items.append(f"Scale mail armor {bns:+}")
            elif _ == 3:
                items.append(f"Lamellar mail armor {bns:+}")
            elif _ == 4:
                items.append(f"Chain mail armor {bns:+}")
            elif _ == 5:
                items.append(f"Light plate mail armor {bns:+}")
            else:
                items.append(f"Heavy plate mail armor {bns:+}")
        items.append(f"Boots of Clumsiness, Rogue: {bns:+}")
        bns = - r.randint(1, 3)
        items.append(f"Gauntlets of Sapping Strength, Warrior: {bns:+}")
        bns = - r.randint(1, 3)
        items.append(f"Ring of Clumsiness, Rogue: {bns:+}")
        items.append("Ring of Slowness, Rogue: -1")
        d100 = r.randint(1, 100)
        bns = -1 if d100 < 75 else -2 if d100 < 96 else -3
        if d6 <= 3:
            # Bladed
            _ = r.randint(1, 6)
            if _ <= 4:
                items.append(f"Sword {bns:+}")
            elif _ == 5:
                items.append(f"Dagger {bns:+}")
            else:
                items.append(f"Two-Handed Sword {bns:+}")
        elif d6 == 4:
            # Bludgeon
            _ = r.randint(1, 6)
            if _ <= 3:
                items.append(f"Warhammer {bns:+}")
            elif _ <= 5:
                items.append(f"Mace {bns:+}")
            else:
                items.append(f"Two-handed Warhammer {bns:+}")
                items.append(f"Two-handed Mace {bns:+}")
        elif d6 == 5:
            # Bow
            _ = r.randint(1, 6)
            if _ <= 4:
                items.append(f"Short bow {bns:+}")
            else:
                items.append(f"Long bow {bns:+}")
        else:
            # Other
            _ = r.randint(1, 6)
            if _ <= 2:
                items.append(f"Axe {bns:+}")
            elif _ <= 5:
                items.append(f"Spear {bns:+}")
            else:
                items.append(f"Two-handed axe {bns:+}")
    return r.choice(items)
