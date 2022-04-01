import random
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from enum import auto

import gamebook_core
from character_sheet import CharacterSheet
from equipment import Armor
from equipment import Item
from equipment import Money
from equipment import Shield
from equipment import Weapon
from gb_utils import get_loot
from gb_utils import intervention
from npcs import NPC

_mob_counter: int = 0


@dataclass
class MobUnit(gamebook_core.AbstractItem):
    """
    This class is to simplify mob vs mob combat with WyRM style character classes.

    Inspired by Dungeon Master's guide (2014) pg 250
    """

    _units: list[CharacterSheet] = field(default_factory=list)
    _name: str | None = None
    _counter: int = 0
    _massive_attack_used: bool = False
    _loot: list[Item | Weapon | Armor | Shield | str] = field(default_factory=list)

    def combat_round(self, opponent_mob: "MobUnit", have_initiative: bool | None = None) -> list[str] | None:
        if isinstance(opponent_mob, CharacterSheet):
            _ = opponent_mob
            opponent_mob = MobUnit()
            opponent_mob.add_unit(_)
        combat_log: list[str] = list()
        starting_hp: dict[str, int] = dict()
        for unit in self._units:
            starting_hp[unit.name_with_id] = unit.hp
        for unit in opponent_mob._units:
            starting_hp[unit.name_with_id] = unit.hp

        if have_initiative is None:
            have_initiative = self.initiative_check(opponent_mob)

        if not self.units or not opponent_mob.units:
            return None

        attacking_mob: MobUnit
        defending_mob: MobUnit
        if have_initiative:
            attacking_mob = self
            defending_mob = opponent_mob
        else:
            attacking_mob = opponent_mob
            defending_mob = self

        defending_hp: int = defending_mob.hp

        if not attacking_mob.is_alive or not defending_mob.is_alive:
            return None

        hit: bool = gamebook_core.dice_roll(1, 6) + attacking_mob.attack >= defending_mob.defense
        combat_result: str = ""
        if hit:
            damage_die: str = attacking_mob.damage_die
            damage_result: str = defending_mob._take_damage(damage_die)
            if damage_result:
                combat_result = damage_result  # f"; {damage_result}{extra}"
            all_units: list[CharacterSheet] = list()
            all_units.extend(self.units)
            all_units.extend(opponent_mob.units)
            for unit in all_units:
                if starting_hp[unit.name_with_id] != unit.hp:
                    hp_lost: int = unit.hp - starting_hp[unit.name_with_id]
                    died_text: str = "" if unit.is_alive else ", DIED."
                    combat_log.append(f"- {unit.name}: {hp_lost:+,} HP{died_text}")
            if combat_result:
                combat_log.append(combat_result)
        return combat_log

    def combat(self, opponent_mob: "MobUnit", have_initiative: bool | None = None) -> list[str] | None:
        if isinstance(opponent_mob, CharacterSheet):
            _ = opponent_mob
            opponent_mob = MobUnit()
            opponent_mob.add_unit(_)

        if not self.is_alive or not opponent_mob.is_alive:
            return None

        combat_log: list[str] = list()
        combat_log.append(f"#### Combat")

        if "Player" not in self.name:
            combat_log.append("")
            # combat_log.append(f"**{self.name}**")
            # combat_log.append("")
            for unit in self.units:
                combat_log.append(f"* {unit.name}")
            combat_log.append("")

        if "Player" not in self.name and "Player" not in opponent_mob.name:
            combat_log.append("*vs*")

        if "Player" not in opponent_mob.name:
            combat_log.append("")
            # combat_log.append(f"**{opponent_mob.name}**")
            # combat_log.append("")
            for unit in opponent_mob.units:
                combat_log.append(f"* {unit.name}")

        combat_log.append("")
        if have_initiative is None:
            have_initiative = self.initiative_check(opponent_mob)

        if have_initiative:
            combat_log.append(f"- {self.name} has initiative.")
        else:
            combat_log.append(f"- {opponent_mob.name} has initiative.")

        while self.is_alive and opponent_mob.is_alive:
            result: list[str] = self.combat_round(opponent_mob, have_initiative=have_initiative)
            if result:
                combat_log.extend(result)
            have_initiative = not have_initiative
            if not opponent_mob.is_alive or not self.is_alive:
                _ = opponent_mob if self.is_alive else self
                if _.fate:
                    starting_fate: dict[str, int] = dict()
                    for unit in _.units:
                        starting_fate[unit.name_with_id] = unit.fate
                    combat_log.append(_.fate_dec(1))
                    # for unit in _.units:
                    #     unit.hp = unit.hit_points_max
        return combat_log

    def initiative_check(self, opponent_mob: "MobUnit", have_initiative: bool | None = None) -> bool:
        opponent_mob: MobUnit | CharacterSheet | list[CharacterSheet]
        if isinstance(opponent_mob, list):
            mob = MobUnit()
            mob.add_units(opponent_mob)
            opponent_mob = mob
        if isinstance(opponent_mob, CharacterSheet):
            mob = MobUnit()
            mob.add_unit(opponent_mob)
            opponent_mob = mob
        roll1: int = gamebook_core.dice_roll(1, 6, True) + self.rogue
        roll2: int = gamebook_core.dice_roll(1, 6, True) + opponent_mob.rogue
        if roll1 > roll2:
            return True
        if roll1 < roll2:
            return False
        return self.initiative_check(opponent_mob)

    @property
    def fate(self) -> int:
        _ = 0
        for unit in self.units:
            _ = max(unit.fate, _)
        return _

    @fate.setter
    def fate(self, new_value: int) -> None:
        if new_value > self.fate:
            for unit in self.units:
                if unit.fate >= self.fate:
                    unit.fate = new_value
        else:
            diff_fate: int = self.fate - new_value
            for unit in self.units:
                unit.fate -= diff_fate
                if unit.fate < 0:
                    unit.fate = 0

    def fate_dec(self, fate: int) -> str:
        if not self.fate:
            return ""
        self.fate -= fate
        if self.fate:
            return f"\nFATE {-fate:+}. FATE POINTS REMAINING: {self.fate}.\n\n; {intervention()}"
        return f"\nFATE {-fate:+}. NO FATE POINTS REMAINING.\n\n; {intervention()}"

    @property
    def xp(self) -> int:
        _ = 0
        for unit in self.units:
            _ += unit.xp
        return _

    @property
    def loot(self) -> list[Item | Weapon | Armor | Shield | Money | str]:
        if self._loot:
            return self._loot
        challenge: int = self.xp // 100
        result = get_loot(challenge)
        self._loot = result
        return result

    @property
    def massive_attack(self) -> bool:
        yes: int = 0
        no: int = 0
        for unit in self.units:
            if unit.massive_attack:
                yes += 1
            else:
                no += 1
        return yes > no

    @property
    def hp_max(self) -> int:
        _ = 0
        for unit in self.units:
            _ += unit.hit_points_max
        return _

    def add_unit(self, unit: CharacterSheet) -> str:
        self.units.append(unit)
        return self.name

    def add_units(self, units: list[CharacterSheet]) -> str:
        if isinstance(units, MobUnit):
            units = units.units
        self.units.extend(units)
        return self.name

    def remove_unit(self, unit: CharacterSheet) -> str:
        idx: int = self.units.index(unit) if unit in self.units else -1
        if idx < 0:
            return "UNIT NOT FOUND"
        return self.units.pop(idx).name

    @property
    def units(self) -> list["CharacterSheet"]:
        return self._units

    @units.setter
    def units(self, units: list["CharacterSheet"]) -> None:
        if not self.units:
            self._name = "Vapors"
        if units:
            for unit in units:
                if unit.is_alive:
                    self._name = unit.base_name
                    break
        self._units = units

    @property
    def name(self) -> str:
        if self.unit_count and not self._name:
            self._name = self.units[0].name
        if self.unit_count == 1:
            return f"{self._name}"
        if self.unit_count == 2:
            return f"The pair led by the {self._name}"
        return f"The group led by the {self._name}"

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    def _take_damage(self, die: str) -> str:
        dmg: int = max(int(gamebook_core.dice_roll2(f"{die}")), 1)
        r_units: list[CharacterSheet] = self._units.copy()
        random.shuffle(r_units)
        unit_count = self.unit_count
        for unit in r_units:
            if unit.is_alive:
                unit_dmg = min(unit.hp, dmg)
                unit.hit_points -= unit_dmg
                dmg -= unit_dmg
        units_lost = unit_count - self.unit_count
        if not units_lost:
            return ""
        if self.alive_count:
            return f"{self.name} lost {units_lost:,} units. {self.alive_count:,} units remaining. (HP: {self.hp})"
        return f"{self.name} lost {units_lost:,} units. No units remaining."

    @property
    def alive_count(self) -> int:
        _ = 0
        for u in self.units:
            if u.is_alive:
                _ += 1
        return _

    def take_damage(self, die: str) -> list[str]:
        result: list[str] = list()
        starting_hp: dict[str, int] = dict()
        for unit in self._units:
            starting_hp[unit.name_with_id] = unit.hp
        self._take_damage(die)
        for unit in self.units:
            if starting_hp[unit.name_with_id] != unit.hp:
                hp_lost: int = unit.hp - starting_hp[unit.name_with_id]
                died_text: str = "" if unit.is_alive else ", DIED."
                result.append(f"- {unit.name}: {hp_lost:+,} HP{died_text}")
        return result

    def take_damage_each(self, die: str) -> list[str]:
        result: list[str] = list()
        starting_hp: dict[str, int] = dict()
        for unit in self._units:
            starting_hp[unit.name_with_id] = unit.hp
        for unit in self.units:
            unit.hp = unit.hp - int(gamebook_core.dice_roll2(die))
        for unit in self.units:
            if starting_hp[unit.name_with_id] != unit.hp:
                hp_lost: int = unit.hp - starting_hp[unit.name_with_id]
                died_text: str = "" if unit.is_alive else ", DIED."
                result.append(f"- {unit.name}: {hp_lost:+,} HP{died_text}")
        return result

    @property
    def is_alive(self) -> bool:
        return self.unit_count > 0

    @property
    def unit_count(self) -> int:
        _ = 0
        for unit in self._units:
            if unit.is_alive:
                _ += 1
        return _

    @property
    def hp(self) -> int:
        _ = 0
        for unit in self._units:
            if unit.is_alive:
                _ += unit.hp
        return _

    @property
    def attack(self) -> int:
        _ = 0
        for unit in self._units:
            if unit.is_alive:
                _ = max(_, unit.attack)
        return _

    @property
    def defense(self) -> int:
        _ = 0
        for unit in self._units:
            if unit.is_alive:
                _ = max(_, unit.defense)
        return _

    @property
    def damage(self) -> int:
        return gamebook_core.dice_roll2(f"{self.damage_die}")

    @property
    def damage_max(self) -> int:
        dmg = self.damage_die.replace("x", "")
        return gamebook_core.dice_roll2_max(dmg)

    @property
    def damage_min(self) -> int:
        dmg = self.damage_die.replace("x", "")
        return gamebook_core.dice_roll2_min(dmg)

    @property
    def damage_die(self) -> str:
        die_max = "1d2"
        val_max: int = 0
        for unit in self._units:
            if unit.is_alive:
                unit_damage = unit.damage.replace("x", "")
                if unit_damage:
                    try:
                        test_val_max: int = int(gamebook_core.dice_roll2_max(unit_damage))
                    except RecursionError as e:
                        print(f"Max Dice Fail: {unit_damage} | {unit.damage}")
                        test_val_max = 0
                    if test_val_max > val_max:
                        val_max = test_val_max
                        die_max = f"{unit.damage} + " * self.unit_count
        if self.massive_attack and not self._massive_attack_used:
            die_max = f"{die_max} {self.warrior} + "
            self._massive_attack_used = True
        return f"{die_max}0"

    @property
    def warrior(self) -> int:
        s: int = 0
        for unit in self._units:
            if unit.is_alive:
                s = max(unit.warrior, s)
        return s

    @property
    def rogue(self) -> int:
        s: int = 0
        for unit in self._units:
            if unit.is_alive:
                s = max(unit.rogue, s)
        return s

    @property
    def mage(self) -> int:
        s: int = 0
        for unit in self._units:
            if unit.is_alive:
                s = max(unit.mage, s)
        return s


class AttackOption(Enum):
    Attack: int = auto()
    Dash: int = auto()
    Defend: int = auto()
    Disengage: int = auto()
    Guard: int = auto()


class MassCombatUnit:
    _cr: int = 0
    _br: int = 0
    _moral: int = 0
    _initiative: int = 10

    @property
    def initiative(self) -> int:
        return self._initiative

    @property
    def moral(self) -> int:
        return self._moral

    @property
    def cr(self) -> int:
        return self._cr

    @property
    def br(self) -> int:
        return self._br


class MassCombat:
    """
    Based on Dungeon Master's Guide (2014), page 250
    and on Unearthed Arcana: Mass Combat [Playtest Material] (2017)
    """
    pass


def mob_combat(group1: list[CharacterSheet], group2: list[CharacterSheet]) -> list[str]:
    if isinstance(group1, CharacterSheet):
        group1 = [group1]
    if isinstance(group2, CharacterSheet):
        group2 = [group2]

    m1: MobUnit = MobUnit()
    m2: MobUnit = MobUnit()

    m1.units = group1
    m2.units = group2

    return m1.combat(m2)


def main():
    units = [NPC.giant_weasel(), NPC.giant_weasel(), NPC.giant_weasel()]
    mob = MobUnit()
    mob.units = units
    print(f"Units: {mob.unit_count}, Total HP: {mob.hp}")
    print(f"Attack: {mob.attack}, Defense: {mob.defense}")
    print("")

    units2 = [NPC.zombie(), NPC.zombie(), NPC.zombie()]
    mob2 = MobUnit()
    mob2.units = units2
    print(f"Units: {mob2.unit_count}, Total HP: {mob2.hp}")
    print(f"Attack: {mob2.attack}, Defense: {mob2.defense}")
    print("")

    have_initiative: bool = mob.initiative_check(mob2)
    for line in mob.combat(mob2, have_initiative):
        print(line)


if __name__ == '__main__':
    main()
