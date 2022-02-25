import random

import dice
import jsonpickle

import character_sheet
from equipment import Armor
from equipment import Item
from equipment import Shield
from equipment import Weapon
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


def intervention() -> str:
    check: int = roll("1d6+1d6+1d6")
    "3,4, 5,6, 7,8, 9,10, 11,12, 13,14, 15,16, 17,18"
    if check <= 4:
        return f"""
; Dark Power Intervention ({check}).
{dark_power_intervention_text()}
"""
    if check <= 6:
        effect: str = random.choice(["Roof collapse.", "Hidden floor pit full of spikes triggers. (3d6 dmg).",
                                     "Spontaneous Combustion. (2d8 dmg).",
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
        return f" ({check})"
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
            return f"PASS {check} >= {difficulty.value}" if check >= difficulty.value else f"FAIL {check} < {difficulty.value}"
        _ += f"{difficulty.name} ({difficulty.value}); "
    return f"{difficulty_name} unknown. {_}"


def stat_check(stat: int, bonus: int) -> bool:
    check: int = roll(f"1d6x + {bonus}")
    return check >= stat


def wander(die: int = 6, yes_if_under: int = 2) -> str:
    yes: bool = roll(f"1d{die}") < yes_if_under
    return random_encounter(yes_if_under - 1) if yes else ""


def random_encounter(c: int) -> str:
    choices: list[str] = list()
    d2: int = roll(f"{c}d2")
    d3: int = roll(f"{c}d3")
    d4: int = roll(f"{c}d4")
    d6: int = roll(f"{c}d6")
    d8: int = roll(f"{c}d8")
    d10: int = roll(f"{c}d10")

    choices.append(f"{d4} giant beetles")
    choices.append(f"{d3} skeleton warriors")
    choices.append(f"{d2} zombies")
    choices.append(f"{d3} giant rats")
    choices.append(f"{d2} spiders")
    choices.append(f"{d10} awakened shrubs")
    choices.append(f"{d2} giant lizards")
    choices.append(f"{d4} giant weasals")
    choices.append(f"{d2} goblin warriors")
    choices.append(f"{d2} hobgoblin warriors")
    choices.append(f"{d4} kobold warriors")
    choices.append(f"{d2} worgs")
    choices.append(loot())
    return random.choice(choices)


def initiative(player_bonus = None,  #
               npc_bonus = None) -> str:
    player_bonus: int | character_sheet.CharacterSheet | None
    npc_bonus: int | character_sheet.CharacterSheet | None
    name1: str = "Player"
    name2: str = "NPC"
    if player_bonus is None:
        player_bonus = 0
    if npc_bonus is None:
        npc_bonus = 0
    if isinstance(player_bonus, character_sheet.CharacterSheet):
        name1 = player_bonus.name
        player_bonus = player_bonus.rogue
    if isinstance(npc_bonus, character_sheet.CharacterSheet):
        name2 = npc_bonus.name
        npc_bonus = npc_bonus.rogue
    if roll(f"1d6+{player_bonus}") > roll(f"1d6+{npc_bonus}"):
        return f"First Character ({name1})"
    if roll(f"1d6+{player_bonus}") < roll(f"1d6+{npc_bonus}"):
        return f"Second Character ({name2})"
    return initiative(player_bonus, npc_bonus)


def initiative_check(player_bonus: int = 0, npc_bonus: int = 0) -> bool:
    if roll(f"1d6+{player_bonus}") > roll(f"1d6+{npc_bonus}"):
        return True
    if roll(f"1d6+{player_bonus}") < roll(f"1d6+{npc_bonus}"):
        return False
    return initiative_check(player_bonus, npc_bonus)


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
        items.append(f"Amulet of Health, MAX HP: {bns:+}")
        d100 = r.randint(1, 100)
        bns = 1 if d100 < 75 else 2 if d100 < 96 else 3
        items.append(f"Armor {bns:+}")
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
        items.append("Potion of Vitality")
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
        items.append(f"Weapon {bns:+}")
    else:
        bns = - r.randint(1, 3)
        items.append(f"Amulet of Weakness, Max HP: {bns:+}")
        d100 = r.randint(1, 100)
        bns = -1 if d100 < 75 else -2 if d100 < 96 else -3
        items.append(f"Armor of Slowness, Rogue: {bns:+}")
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
        bns = - r.randint(1, 3)
        items.append(f"Ring of Clumsiness, Rogue: {bns:+}")
        items.append("Ring of Slowness, Defense: -1")
        d100 = r.randint(1, 100)
        bns = -1 if d100 < 75 else -2 if d100 < 96 else -3
        items.append(f"Cursed Weapon {bns:+}")
    return r.choice(items)


