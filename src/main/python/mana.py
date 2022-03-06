import jsonpickle

from skills import *


@dataclass(slots=True)
class MageSpell:
    _name: str = ""
    description: str = ""
    circle: int = 0
    mana_cost: int = 0
    difficulty: Difficulty = None
    macro: list[str] = field(default_factory=list)
    is_scroll: bool = False

    @property
    def as_scroll(self) -> "MageSpell":
        scroll = self.copy()
        scroll.is_scroll = True
        return scroll

    @property
    def as_spell(self) -> "MageSpell":
        spell = self.copy()
        spell.is_scroll = False
        return spell

    @property
    def name(self) -> str:
        if self.is_scroll:
            return f"{self._name} Scroll"
        return f"{self._name} Spell"

    def __init__(self, circle: int = 1, name: str = "", description: str = ""):
        if circle < 1:
            circle = 1
        self.is_scroll = False
        self.circle = circle
        self._name = name
        self.description = description
        self.macro = list()

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

    def __copy__(self) -> "MageSpell":
        return jsonpickle.decode(jsonpickle.encode(self))

    def copy(self) -> "MageSpell":
        return self.__copy__()

    def __lt__(self, other):
        # if self.circle != other.circle:
        #     return self.circle < other.circle
        return self.name < other.name

    def __str__(self):
        return f"{self.name}, Mana: {self.mana_cost}, Difficulty: {self.difficulty}, {self.description}"


@dataclass(slots=True)
class MageSpellList:

    @classmethod
    def spells(cls) -> list[MageSpell]:
        mage_spells: list[MageSpell] = list()
        mage_spells.append(MageSpell(1, "Frost Burn", "Touch. 1d6-2 damage. Mana burn raises damage by +1."))
        healing_hand = MageSpell(1, "Healing Hand", "Touch. 2d3 HP healed. Mana burn raises heal by +1.")
        healing_hand.macro.append("@hp: roll('2d3')")
        healing_hand.macro.append("@pc_id.hp: player.hp_add(hp)")
        healing_hand.macro.append(f"@pc_id.mana: player.mana - {healing_hand.mana_cost}")
        mage_spells.append(healing_hand)
        mage_spells.append(MageSpell(1, "Magic Light", "Create a magic light on the tip of a staff or other "
                                                            "weapon. 10 yard radius."
                                                            " Duration: 1 hour + 1 mana per additional hour."
                                                            " Options: Ball of light (form "
                                                            "into a ball that can be controlled with thought), "
                                                            "Colored light (select any visible color), Light beam ("
                                                            "tight beam up to 15 yards). Bright Flash (Effect ends "
                                                            "after 1 round. Blinds anyone unprotected for 1d6 "
                                                            "rounds."))
        mage_spells.append(MageSpell(1, "Sense Magic", "Sense magic in a 3 yard radius. Mana burn +1 yard."))
        mage_spells.append(MageSpell(1, "Telekinesis", "Remotely move one item up to 1kg. Duration: 1 min. Mana "
                                                            "burn +1kg."))
        mage_spells.append(MageSpell(2, "Food and Water", "1 Daily ration of food and water."))
        mage_spells.append(MageSpell(2, "Healing Light", "Touch. Heal 1d6 HP. Mana burn: +2 HP."))
        mage_spells.append(MageSpell(2, "Identify", "Identify one magic property of an item. Mana burn: one "
                                                         "additional property."))
        mage_spells.append(MageSpell(2, "Levitation", "Slowly float up and down for 3 minutes. May be sustained "
                                                           "for 1 mana per minute. No propulsion provided."))
        mage_spells.append(MageSpell(2, "Lightning Bolt", "Missile attack. 1d6+2 damage. Mana burn: +2 damage."))
        mage_spells.append(MageSpell(2, "Magic Armor", "Shield. Will last until shield's HP is consumed. 4 HP. "
                                                            "Mana burn: 4 HP. Excess damage is discarded."))
        mage_spells.append(MageSpell(3, "Chain Lightning", "Missile attack. Up to 3 targets in a 3 yard radius. "
                                                                "3d6 damage. Mana burn: damage +2 or radius +2 "
                                                                "yards."))
        mage_spells.append(MageSpell(3, "Walk on Air", "Walk on air is if solid ground. Duration: 3 minutes. "
                                                            "Sustained for 1 minute for 1 mana."))
        mage_spells.append(MageSpell(3, "Fire Bolt", "Missile. 3d6 damage. Radius of 3 yards. Mana burn: damage "
                                                          "+2 or radius + 2 yards."))
        mage_spells.append(MageSpell(3, "Enchant Weapon", "Grants +2 on attack rolls and damage. Last for one "
                                                               "combat encounter. Mana burn: +1 to attack and "
                                                               "damage."))
        mage_spells.append(MageSpell(3, "Stasis", "Touch. Freezes target for number of hours equal to successes "
                                                       "rolled."))
        mage_spells.append(MageSpell(4, "Summon Earth Elemental", "Summons. Raises an earth elemental. Remains "
                                                                       "until dispelled or HP is exhausted."))
        mage_spells.append(MageSpell(4, "Magic Step", "Teleport up to 10 yards. Mana burn: +10 yards. Must have "
                                                           "a clear mental image of destination."))
        mage_spells.append(MageSpell(4, "Moon Gate", "Can open a moongate at special locations such as stone "
                                                          "circles. Moongates allow instant travel over long "
                                                          "distances. Closes slowly after 2 minutes. Mana burn: Not "
                                                          "available."))
        mage_spells.append(MageSpell(4, "Return to Life", "Touch. Revive one fallen character. Character is "
                                                               "restored with 2 HP. Mana burn: +2 HP restored. Body "
                                                               "must still be 'warm'."))
        mage_spells.append(MageSpell(4, "Summon Phantom Steed", "Summons. Raises a phantom steed. Duration: 24 "
                                                                     "hours or until dispelled or HP is exhausted. "
                                                                     "Mana burn: Not available."))
        return mage_spells

    @classmethod
    def random_spell(cls, mana: int | None = None, circle: int | None = None) -> MageSpell:
        if circle is not None:
            mana = 2 ** (circle - 1)
        if mana is None:
            mana = 1
        spells: list[MageSpell] = cls.spells()
        while True:
            spell: MageSpell = random.choice(spells)
            if spell.mana_cost <= mana and random.randint(1, 10) > spell.mana_cost:
                return spell

    @classmethod
    def by_name(cls, name: str) -> MageSpell | None:
        spells: list[MageSpell] = cls.spells()
        for spell in spells.copy():
            spells.append(spell.as_scroll)
        for spell in spells:
            if name.lower() in spell.name.lower():
                return spell
        return None

    @classmethod
    def spell_by_name(cls, name: str) -> MageSpell | None:
        return cls.by_name(name)


