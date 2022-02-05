from dataclasses import dataclass
from skills import *


@dataclass(slots=True)
class MageSpell:
    name: str = ""
    description: str = ""
    circle: int = 0
    mana_cost: int = 0
    difficulty: Difficulty = None

    def __init__(self, circle: int = 1, name: str = "", description: str = ""):
        if circle < 1:
            circle = 1

        self.circle = circle
        self.name = name
        self.description = description

        if circle == 1:
            self.mana_cost = 1
            self.difficulty = Difficulty.Easy
        elif circle == 2:
            self.mana_cost = 2
            self.difficulty = Difficulty.Routine
        elif circle == 3:
            self.mana_cost = 4
            self.difficulty = Difficulty.Challenging
        elif circle == 4:
            self.mana_cost = 8
            self.difficulty = Difficulty.Extreme
        else:
            self.mana_cost = 2 ** circle
            self.difficulty = Difficulty.Extreme

    def __lt__(self, other):
        # if self.circle != other.circle:
        #     return self.circle < other.circle
        return self.name < other.name

    def __str__(self):
        return f"{self.name}, Mana: {self.mana_cost}, Difficulty: {self.difficulty}, {self.description}"


@dataclass(slots=True)
class MageSpellList:
    mage_spells: list[MageSpell] = field(default_factory=list)

    def __post_init__(self):
        self.mage_spells.append(MageSpell(1, "Frost Burn", "Touch. 1d6-2 damage. Mana burn raises damage by +1."))
        self.mage_spells.append(MageSpell(1, "Healing Hand", "Touch. 1d6 HP healed. Mana burn raises heal by +1."))
        self.mage_spells.append(MageSpell(1, "Magic Light", "Create a magic light on the tip of a staff or other "
                                                            "weapon. 10 yard radius."
                                                            " Duration: 1 hour + 1 mana per additional hour."
                                                            " Options: Ball of light (form "
                                                            "into a ball that can be controlled with thought), "
                                                            "Colored light (select any visible color), Light beam ("
                                                            "tight beam up to 15 yards). Bright Flash (Effect ends "
                                                            "after 1 round. Blinds anyone unprotected for 1d6 "
                                                            "rounds."))
        self.mage_spells.append(MageSpell(1, "Sense Magic", "Sense magic in a 3 yard radius. Mana burn +1 yard."))
        self.mage_spells.append(MageSpell(1, "Telekinesis", "Remotely move one item up to 1kg. Duration: 1 min. Mana "
                                                            "burn +1kg."))
        self.mage_spells.append(MageSpell(2, "Food and Water", "1 Daily ration of food and water."))
        self.mage_spells.append(MageSpell(2, "Healing Light", "Touch. Heal 1d6 HP. Mana burn: +2 HP."))
        self.mage_spells.append(MageSpell(2, "Identify", "Identify one magic property of an item. Mana burn: one "
                                                         "additional property."))
        self.mage_spells.append(MageSpell(2, "Levitation", "Slowly float up and down for 3 minutes. May be sustained "
                                                           "for 1 mana per minute. No propulsion provided."))
        self.mage_spells.append(MageSpell(2, "Lightning Bolt", "Missile attack. 1d6+2 damage. Mana burn: +2 damage."))
        self.mage_spells.append(MageSpell(2, "Magic Armor", "Shield. Will last until shield's HP is consumed. 4 HP. "
                                                            "Mana burn: 4 HP. Excess damage is discarded."))
        self.mage_spells.append(MageSpell(3, "Chain Lightning", "Missile attack. Up to 3 targets in a 3 yard radius. "
                                                                "3d6 damage. Mana burn: damage +2 or radius +2 "
                                                                "yards."))
        self.mage_spells.append(MageSpell(3, "Walk on Air", "Walk on air is if solid ground. Duration: 3 minutes. "
                                                            "Sustained for 1 minute for 1 mana."))
        self.mage_spells.append(MageSpell(3, "Fire Bolt", "Missile. 3d6 damage. Radius of 3 yards. Mana burn: damage "
                                                          "+2 or radius + 2 yards."))
        self.mage_spells.append(MageSpell(3, "Enchant Weapon", "Grants +2 on attack rolls and damage. Last for one "
                                                               "combat encounter. Mana burn: +1 to attack and "
                                                               "damage."))
        self.mage_spells.append(MageSpell(3, "Stasis", "Touch. Freezes target for number of hours equal to successes "
                                                       "rolled."))
        self.mage_spells.append(MageSpell(4, "Summon Earth Elemental", "Summons. Raises an earth elemental. Remains "
                                                                       "until dispelled or HP is exhausted."))
        self.mage_spells.append(MageSpell(4, "Magic Step", "Teleport up to 10 yards. Mana burn: +10 yards. Must have "
                                                           "a clear mental image of destination."))
        self.mage_spells.append(MageSpell(4, "Moon Gate", "Can open a moongate at special locations such as stone "
                                                          "circles. Moongates allow instant travel over long "
                                                          "distances. Closes slowly after 2 minutes. Mana burn: Not "
                                                          "available."))
        self.mage_spells.append(MageSpell(4, "Return to Life", "Touch. Revive one fallen character. Character is "
                                                               "restored with 2 HP. Mana burn: +2 HP restored. Body "
                                                               "must still be 'warm'."))
        self.mage_spells.append(MageSpell(4, "Summon Phantom Steed", "Summons. Raises a phantom steed. Duration: 24 "
                                                                     "hours or until dispelled or HP is exhausted. "
                                                                     "Mana burn: Not available."))

    @classmethod
    def random_spell(cls, mana: int = 1) -> MageSpell:
        while True:
            spell: MageSpell = random.choice(MageSpellList().mage_spells)
            if spell.mana_cost <= mana and random.randint(1, 10) > spell.mana_cost:
                return spell

    @classmethod
    def spell_by_name(cls, name: str) -> MageSpell | None:
        for spell in MageSpellList().mage_spells:
            if name.lower() == spell.name.lower():
                return spell
        return None



