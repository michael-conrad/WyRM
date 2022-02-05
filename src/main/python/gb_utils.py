import random

import dice
import jsonpickle

from character_sheet import CharacterSheet
from skills import Difficulty


def debug(object: any) -> str:
    s: str = str(object)
    print(f"DEBUG: {s}")
    return s


def unpickle(pickled: str) -> any:
    return jsonpickle.decode(pickled)


def attack(attack_attribute: int = 0, defense: int = 0) -> str:
    check: int = roll(f"1d6+{attack_attribute}")
    return f"Success ({check}>={defense})" if check >= defense else f"Fail ({check}<{defense})"


def damage_against(sheet: CharacterSheet, die: str = "1d6", extra_damage: str = "") -> (int, int):
    damage: int = roll(f"{die} + {extra_damage}")
    if sheet.hit_points_armor:
        sheet.hit_points_armor -= damage
        if sheet.hit_points_armor < 0:
            sheet.hit_points -= (-sheet.hit_points_armor//2)
            sheet.hit_points_armor = 0
        return sheet.hit_points, sheet.hit_points_armor
    sheet.hit_points -= damage
    if sheet.hit_points < 0:
        sheet.hit_points = 0
    return sheet.hit_points, sheet.hit_points_armor


def roll(die: str) -> int:
    if die.strip()[-1] != "t":
        die += " t"
    return int(dice.roll(f"{die}"))


def dl_check(difficulty_name: str, bonus: int) -> str:
    _: str = ""
    for difficulty in Difficulty:
        if difficulty.name.lower() == difficulty_name.lower():
            die_value: int = roll("1d6x")
            check: int = die_value + bonus
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
    choices.append("2d4 spiders")
    choices.append("2d4 giant rats")
    choices.append("1 giant beetle")
    choices.append("1d5 skeletons")
    choices.append("1d3 zombies")
    choices.append("loot")
    return random.choice(choices)


def initiative(player_bonus: int = 0, npc_bonus: int = 0):
    player_is_winner: bool = roll(f"1d6+{player_bonus}") >= roll(f"1d6+{npc_bonus}")
    return "PLAYER" if player_is_winner else "NPC"
