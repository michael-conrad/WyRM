import random
from dataclasses import dataclass
from dataclasses import field
from skills import SkillAttribute


@dataclass(slots=True)
class CharacterTalent:
    name: str = ""
    description: str = ""
    skill_attributes: list[SkillAttribute] = field(default_factory=list)
    stackable: bool = False

    def __init__(self, name: str = "",  #
                 description: str = "",  #
                 skill_attributes: list[SkillAttribute] = None,  #
                 stackable: bool = False):
        self.name = name
        self.description = description
        if skill_attributes:
            self.skill_attributes = skill_attributes.copy()
        else:
            self.skill_attributes = list()
        self.stackable = stackable

    def __str__(self):
        return f"{self.name}: {self.description}"


@dataclass(slots=True)
class TalentList:
    talents: list[CharacterTalent] = field(default_factory=list)

    def __post_init__(self):
        self.talents.append(CharacterTalent("Armored Caster", "Reduce armor penalty -2. May be stacked.", [SkillAttribute.Mage], True))
        self.talents.append(CharacterTalent("Blood Mage", "May use Hit Points instead of Mana for casting spells.", [SkillAttribute.Mage]))
        self.talents.append(CharacterTalent("Champion", "Select a cause. +2 on attack and damage against enemies of "
                                                        "the cause. May be stacked.", None, True))
        self.talents.append(CharacterTalent("Channeller", "Add Mage attribute level to magic attack once per combat.", [SkillAttribute.Mage]))
        self.talents.append(CharacterTalent("Craftsman", "Trained in one craft such as blacksmithing, carpentry, "
                                                         "bow making, etc. May be stacked.", None, True))
        self.talents.append(CharacterTalent("Dual Wielder", "May wield a weapon in off-hand without penalty. Does not "
                                                            "grant an extra attack.", [SkillAttribute.Rogue, SkillAttribute.Warrior]))
        self.talents.append(CharacterTalent("Familiar", "You have a small animal such as a rat, cat, dog, or bird as a "
                                                        "companion that can do simple tricks.", [SkillAttribute.Mage]))
        self.talents.append(CharacterTalent("Henchman", "You are followed around by one henchman that works as your "
                                                        "squire/pack mule.", [SkillAttribute.Warrior, SkillAttribute.Rogue]))
        self.talents.append(CharacterTalent("Hunter", "You are trained as a hunter and to live off the land. With "
                                                      "enough time, may procure food enough for four.", [SkillAttribute.Warrior, SkillAttribute.Rogue]))
        self.talents.append(CharacterTalent("Leadership", "You are a leader and may command troops.", [SkillAttribute.Warrior]))
        self.talents.append(CharacterTalent("Lucky Devil", "May reroll and roll once per scene or combat."))
        self.talents.append(CharacterTalent("Massive Attack", "You can add your Warrior level to your melee attack "
                                                              "damage once per combat.", [SkillAttribute.Warrior]))
        self.talents.append(CharacterTalent("Precise Shot", "You can add your Rogue level to your ranged attack "
                                                            "damage once per combat.", [SkillAttribute.Rogue]))
        self.talents.append(CharacterTalent("Sailor", "You can steer a boat or sailing ship. No penalties for "
                                                      "fighting on a sea vessel.", [SkillAttribute.Rogue, SkillAttribute.Warrior]))
        self.talents.append(CharacterTalent("Sixth Sense", "You may roll 4+ to become aware of an ambush, etc, before "
                                                           "it occurs and are not surprised."))
        self.talents.append(CharacterTalent("Touch as Nails", "All damage per attack is reduced by -2."))

    def random_talent(self, skill_attribute: SkillAttribute = None):
        if not skill_attribute:
            return random.choice(self.talents)
        while True:
            talent: CharacterTalent = random.choice(self.talents)
            if skill_attribute in talent.skill_attributes:
                return talent

    def matching_random_talent(self, warrior: int, rogue: int, mage: int):
        if warrior >= rogue and warrior >= mage:
            if warrior > rogue and warrior > mage:
                return self.random_talent(SkillAttribute.Warrior)
        if rogue > warrior and rogue > mage:
            return self.random_talent(SkillAttribute.Rogue)
        if mage > warrior and mage > rogue:
            return self.random_talent(SkillAttribute.Mage)
        if warrior and random.choice([True, False, False]):
            return self.random_talent(SkillAttribute.Warrior)
        if rogue and random.choice([True, False, False]):
            return self.random_talent(SkillAttribute.Rogue)
        if mage and random.choice([True, False, False]):
            return self.random_talent(SkillAttribute.Mage)
        return self.random_talent()

















