import random

import dice
import jsonpickle

from equipment import Item
from skills import Difficulty


def debug(object: any) -> str:
    s: str = str(object)
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


def intervention() -> str:
    check: int = roll("1d6+1d6+1d6")
    "3,4, 5,6,7,8, 9,10,11,12, 13,14,15,16, 17,18"
    if check <= 4:
        return f"Dark Power Intervention ({check})."
    if check <= 8:
        return f"Environmental. Lightning. Tunnel collapse. ({check})."
    if check <= 12:
        return f"Opposing forces make a mistake, trip up, get in the way of each other ({check})."
    if check <= 16:
        return f"Opposing forces attack each other or hurt themselves with own weapons ({check})."
    # check >= 17
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
    char_list: str = "\n"
    for key in state:
        var = state[key]
        if isinstance(var, type):
            continue
        if hasattr(var, "is_alive") and hasattr(var, "name"):
            char_list += f";## {key}: {var.name}\n"
    return char_list


def list_items(state: dict) -> str:
    item_list: str = "\n"
    for key in state:
        var = state[key]
        if isinstance(var, type):
            continue
        if isinstance(var, Item) and hasattr(var, "name"):
            item_list += f";##  {key}: {var.name}\n"
    return item_list


def dl_check(difficulty_name: str, attribute_value: int) -> str:
    _: str = ""
    for difficulty in Difficulty:
        if difficulty.name.lower() == difficulty_name.lower():
            die_value: int = roll("1d6x")
            check: int = die_value + attribute_value
            return f"PASS {check} >= {difficulty.value}" if check >= difficulty.value else f"FAIL {check} < {difficulty.value}"
        _ += f"{difficulty.name} ({difficulty.value}); "
    return f"{difficulty_name} unknown. {_}"


def stat_check(stat: int, bonus: int) -> bool:
    check: int = roll(f"1d6x + {bonus}")
    return check >= stat


def random_encounter_check(die: int = 6, yes_if_under: int = 2) -> (bool, str):
    yes: bool = roll(f"1d{die}") < yes_if_under
    return (yes, random_encounter()) if yes else (yes, "")


wander = random_encounter_check


def random_encounter() -> str:
    choices: list[str] = list()
    choices.append("1d2 spiders")
    choices.append("1d3 giant rats")
    choices.append("1 giant beetle")
    choices.append("1d3 skeletons")
    choices.append("1d2 zombies")
    choices.append("loot")
    return random.choice(choices)


def initiative(player_bonus: int = 0, npc_bonus: int = 0) -> str:
    if roll(f"1d6+{player_bonus}") > roll(f"1d6+{npc_bonus}"):
        return "First Character (Player)"
    if roll(f"1d6+{player_bonus}") < roll(f"1d6+{npc_bonus}"):
        return "Second Character (NPC)"
    return initiative(player_bonus, npc_bonus)


def initiative_check(player_bonus: int = 0, npc_bonus: int = 0) -> bool:
    if roll(f"1d6+{player_bonus}") > roll(f"1d6+{npc_bonus}"):
        return True
    if roll(f"1d6+{player_bonus}") < roll(f"1d6+{npc_bonus}"):
        return False
    return initiative_check(player_bonus, npc_bonus)


def loot_box(qty: int = 1) -> list[str]:
    items: list[str] = list()
    while len(items) < qty:
        item: str = "; " + loot()
        if item in items:
            continue
        items.append(item)
    items.sort()
    return items


def loot() -> str:
    items: list[str] = list()
    if dice.roll("1d100t") < 75:
        items.append("Amulet of Health, MAX HP + 3")
        items.append("Armor 1d100 01-75=+1 76-95=+2, 96-00=+3")
        items.append("Bag of Holding")
        items.append("Boots of Striding and Springing, ROGUE +1d3")
        items.append("Cloak of Elvenkind")
        items.append("Gauntlets of Ogre Power, WARRIOR +1d3")
        items.append("Gloves of Swimming and Climbing")
        items.append("Goggles of Night (darkvision 60ft)")
        items.append("Headband of Intellect, MAGE +1d3")
        items.append("Keoghtom's Ointment, doses: 1d4+1, heals 2d8+2")
        items.append("Potion of Flying")
        items.append("Potion of Invisibility")
        items.append("Potion of Vitality")
        items.append("Ring of Evasion, ROGUE +1d3")
        items.append("Ring of Protection, BASE ARMOR +1")
        items.append("Ring of Resistance, 1d10: see pg60 DMBasicRulesv.0.3")
        items.append("Spell Scroll 1d100 01-55=c1 56-80=c2 81-93=c3, 94-00=c4")
        items.append("Wand of Magic Detection, 1d3 uses/day")
        items.append("Wand of Magic Missiles, 1d3 uses/day")
        items.append("Weapon 1d100 00-75%=+1 76-95=+2, 96-00=+3")
    else:
        items.append("Amulet of Weakness, MAX HP -1d3")
        items.append("Armor of Slowness 1d100 01-75=-1 76-95=-2, 96-00=-3 Rogue")
        items.append("Bag of Devouring")
        items.append("Boots of Clumsiness, ROGUE -1d3")
        items.append("Gauntlets of Sapping Strength, WARRIOR -1d3")
        items.append("Headband of Dull Thinking, MAGE -1d3")
        items.append("Keoghtaz's Ointment, doses: 1d4+1, damages 2d8+2")
        items.append("Potion of Health Drain. HP -2d4")
        items.append("Ring of Clumsiness, ROGUE -1d3")
        items.append("Ring of Slowness, DEFENSE -1")
        items.append("Cursed Weapon 1d100 00-75%=-1 76-95=-2, 96-00=-3 ATTACK/DAMAGE")
    return random.choice(items)
