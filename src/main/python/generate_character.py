#!/usr/bin/env bash
"""true" '''\'
set -e
eval "$(conda shell.bash hook)"
conda deactivate
conda activate WyRM
exec python "$0" "$@"
exit $?
''"""
import random

from character_sheet import CharacterSheet
from equipment import Armor
from equipment import Item
from equipment import Weapon
from mana import MageSpell
from mana import MageSpellList
from skills import CharacterSkill
from skills import CharacterSkillsList
from talents import TalentList


def main() -> None:
    r = random.Random()
    sheet: CharacterSheet = CharacterSheet()
    points_remaining: int = 10
    while True:
        choice: str = r.choice(["w", "r", "m"])
        points: int
        max_points: int
        max_points = min(min(points_remaining, 3), 3)
        points = r.randint(0, max_points)
        if choice == "w":
            if sheet.warrior + points <= 6:
                sheet.warrior += points
            else:
                points = 0
        elif choice == "r":
            if sheet.rogue + points <= 6:
                sheet.rogue += points
            else:
                points = 0
        else:
            if sheet.mage + points <= 6:
                sheet.mage += points
            else:
                points = 0
        points_remaining -= points
        if points_remaining < 1:
            break

    sheet.reset_pools()

    skills_list = CharacterSkillsList()
    while len(sheet.skills) < 3:
        skill: CharacterSkill = skills_list.random_skill()
        attribute_level: int = sheet.attribute_level(skill.skill_attribute)
        if attribute_level and skill not in sheet.skills:
            sheet.skills.append(skill)
    sheet.skills.sort()

    sheet.talents.append(TalentList().matching_random_talent(sheet.warrior, sheet.rogue, sheet.mage))

    mana: int = sheet.mana // 2 + 1
    while mana > 0 and len(sheet.spells) < 2:
        spell: MageSpell = MageSpellList().random_spell(mana)
        if spell in sheet.spells:
            continue
        mana -= spell.mana_cost
        sheet.spells.append(spell)
    sheet.spells.sort()

    money_sp: int = 200

    item: Item

    item = Item("Adventurer's Kit", 5)
    sheet.equipment.append(item)
    money_sp -= item.cost_sp

    item = Item("Backpack", 4)
    sheet.equipment.append(item)
    money_sp -= item.cost_sp

    if sheet.mage:
        item = Item("Spellbook", 20)
        sheet.equipment.append(item)
        money_sp -= item.cost_sp

    item = Item("Iron Rations (1 week)", 14)
    sheet.equipment.append(item)
    money_sp -= item.cost_sp

    item = Item("Rations (1 week)", 7)
    sheet.equipment.append(item)
    money_sp -= item.cost_sp

    item = Item("Torches (3)", 3)
    sheet.equipment.append(item)
    money_sp -= item.cost_sp

    if ("Thievery" in sheet.skill_names()  #
            or (sheet.rogue > sheet.warrior and sheet.rogue > sheet.mana)):
        item = Item("Lock Pick", 2)
        sheet.equipment.append(item)
        money_sp -= item.cost_sp

    item = Item("Rope (10 yards)", 2)
    sheet.equipment.append(item)
    money_sp -= item.cost_sp

    item = Item("Common Clothing", 3)
    sheet.equipment.append(item)
    money_sp -= item.cost_sp

    item = Item("Travel Clothing", 3)
    sheet.equipment.append(item)
    money_sp -= item.cost_sp

    if sheet.mage > sheet.warrior and sheet.mage > sheet.rogue:
        item = Item("Noble's Clothing", 12)
        sheet.equipment.append(item)
        money_sp -= item.cost_sp

    item_name = "Cask of Beer"
    item_cost = 6
    if money_sp >= item_cost and random.randint(1, 6) == 1:
        item = Item(item_name, item_cost)
        sheet.equipment.append(item)
        money_sp -= item.cost_sp

    item_name = "Cask of Wine"
    item_cost = 9
    if money_sp >= item_cost and random.randint(1, 6) == 1:
        item = Item(item_name, item_cost)
        sheet.equipment.append(item)
        money_sp -= item.cost_sp

    item_name = "Lantern"
    item_cost = 5
    if money_sp >= item_cost and random.randint(1, 6) == 1:
        item = Item(item_name, item_cost)
        sheet.equipment.append(item)
        money_sp -= item.cost_sp

    item_name = "Pickaxe"
    item_cost = 3
    if money_sp >= item_cost and random.randint(1, 6) == 1:
        item = Item(item_name, item_cost)
        sheet.equipment.append(item)
        money_sp -= item.cost_sp

    # Weapons
    weapons: list[Weapon] = Weapon.list()
    random.shuffle(weapons)
    for weapon in weapons:
        if weapon.cost_sp > money_sp:
            continue
        skill: CharacterSkill = random.choice(sheet.skills)
        if weapon.skill == skill:
            money_sp -= weapon.cost_sp
            sheet.weapons.append(weapon)
            break
    # Armor
    armors: list[Armor] = Armor.list()
    random.shuffle(armors)
    for armor in armors:
        if armor.cost_sp > money_sp:
            continue
        if not sheet.mana_max:
            money_sp -= armor.cost_sp
            sheet.armor_worn.append(armor)
            break
        if armor.armor_penalty < sheet.mana_max // 2:
            money_sp -= armor.cost_sp
            sheet.armor_worn.append(armor)
            break

    # Special Magi stuff
    if sheet.mage > sheet.warrior and sheet.mage > sheet.rogue:
        if money_sp >= 35 and random.randint(1, 6) < 3:
            item = Item("Magic Staff - 1st Circle", 35)
            sheet.equipment.append(item)
            money_sp -= item.cost_sp
        elif money_sp >= 70 and random.randint(1, 6) < 3:
            item = Item("Magic Staff - 2nd Circle", 70)
            sheet.equipment.append(item)
            money_sp -= item.cost_sp
        elif money_sp >= 140 and random.randint(1, 6) < 3:
            item = Item("Magic Staff - 3rd Circle", 35)
            sheet.equipment.append(item)
            money_sp -= item.cost_sp
        elif money_sp >= 250 and random.randint(1, 6) < 3:
            item = Item("Magic Staff - 4th Circle", 250)
            sheet.equipment.append(item)
            money_sp -= item.cost_sp

    if sheet.mage > sheet.warrior or sheet.mage > sheet.rogue:
        if money_sp >= 35 and random.randint(1, 6) < 2:
            item = Item("Magic Ring - 1st Circle", 35)
            sheet.equipment.append(item)
            money_sp -= item.cost_sp
        elif money_sp >= 70 and random.randint(1, 6) < 2:
            item = Item("Magic Ring - 2nd Circle", 70)
            sheet.equipment.append(item)
            money_sp -= item.cost_sp
        elif money_sp >= 140 and random.randint(1, 6) < 2:
            item = Item("Magic Ring - 3rd Circle", 35)
            sheet.equipment.append(item)
            money_sp -= item.cost_sp
        elif money_sp >= 250 and random.randint(1, 6) < 2:
            item = Item("Magic Ring - 4th Circle", 250)
            sheet.equipment.append(item)
            money_sp -= item.cost_sp

    print()
    print("===")
    print()
    sheet.print()
    print("---")
    print()

    print(f"Remaining Money: {money_sp}")


if __name__ == "__main__":
    main()
