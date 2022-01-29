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
from skills import CharacterSkill
from skills import CharacterSkillsList


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

    print()
    print("===")
    print()
    sheet.print()
    print("---")
    print()


if __name__ == "__main__":
    main()
