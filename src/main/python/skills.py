from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from enum import auto
import random


class Difficulty(Enum):
    Easy = 5
    Routine = 7
    Challenging = 9
    Hard = 11
    Extreme = 13

    def __str__(self) -> str:
        return f"{self.name}"


class SkillAttribute(Enum):
    Rogue = auto()
    Mage = auto()
    Warrior = auto()

    def __str__(self) -> str:
        return f"{self.name}"


@dataclass(slots=True)
class DifficultyCheck:
    level: Difficulty = Difficulty.Extreme
    skill: SkillAttribute = SkillAttribute.Warrior

    def __str__(self) -> str:
        return f"{self.skill.name}: {self.level.name} Difficulty"


@dataclass(slots=True)
class CharacterSkill:
    skill_name: str = ""
    skill_attribute: SkillAttribute = None

    def __init__(self, skill_name: str = "", skill_attribute: SkillAttribute = None):
        self.skill_name = skill_name
        self.skill_attribute = skill_attribute

    def __str__(self) -> str:
        return f"{self.skill_name} | {self.skill_attribute}"

    def __lt__(self, other) -> bool:
        return self.skill_name < other.skill_name


@dataclass(slots=True)
class CharacterSkillsList:
    skills_list: list[CharacterSkill] = field(default_factory=list)

    def __post_init__(self):
        self.skills_list.append(CharacterSkill("Acrobatics", SkillAttribute.Rogue))
        self.skills_list.append(CharacterSkill("Alchemy", SkillAttribute.Mage))
        self.skills_list.append(CharacterSkill("Athletics", SkillAttribute.Warrior))
        self.skills_list.append(CharacterSkill("Awareness", SkillAttribute.Mage))
        self.skills_list.append(CharacterSkill("Axes", SkillAttribute.Warrior))
        self.skills_list.append(CharacterSkill("Blunt Weapons", SkillAttribute.Warrior))
        self.skills_list.append(CharacterSkill("Bows", SkillAttribute.Rogue))
        self.skills_list.append(CharacterSkill("Driving", SkillAttribute.Warrior))
        self.skills_list.append(CharacterSkill("Daggers", SkillAttribute.Rogue))
        self.skills_list.append(CharacterSkill("Firearms", SkillAttribute.Rogue))
        self.skills_list.append(CharacterSkill("Herbalism", SkillAttribute.Mage))
        self.skills_list.append(CharacterSkill("Hermeticism", SkillAttribute.Mage))
        self.skills_list.append(CharacterSkill("Lore", SkillAttribute.Mage))
        self.skills_list.append(CharacterSkill("Riding", SkillAttribute.Warrior))
        self.skills_list.append(CharacterSkill("Spears", SkillAttribute.Warrior))
        self.skills_list.append(CharacterSkill("Swords", SkillAttribute.Warrior))
        self.skills_list.append(CharacterSkill("Thaumaturgy", SkillAttribute.Mage))
        self.skills_list.append(CharacterSkill("Thievery", SkillAttribute.Rogue))
        self.skills_list.append(CharacterSkill("Thrown", SkillAttribute.Rogue))
        self.skills_list.append(CharacterSkill("Unarmed", SkillAttribute.Warrior))

    def random_skill(self) -> CharacterSkill:
        return random.choice(self.skills_list)

    def skill_by_name(self, skill_name: str) -> CharacterSkill | None:
        for skill in self.skills_list:
            if skill.skill_name == skill_name:
                return skill
        return None

