import random
from dataclasses import dataclass
from dataclasses import field

import dice
import jsonpickle

from equipment import Armor
from equipment import Item
from equipment import Shield
from equipment import Weapon
from gb_utils import dl_check
from gb_utils import initiative_check
from gb_utils import roll
from mana import MageSpell
from mana import MageSpellList
from skills import CharacterSkill
from skills import SkillAttribute
from talents import CharacterTalent


def copy_of(o) -> any:
    return jsonpickle.decode(jsonpickle.encode(o))


@dataclass(slots=True)
class CharacterSheet:
    _name: str = ""
    location: str = ""
    description: str = ""
    weapons: list[Weapon] = field(default_factory=list)
    armor_worn: list[Armor] = field(default_factory=list)
    skills: list[CharacterSkill] = field(default_factory=list)
    talents: list[CharacterTalent] = field(default_factory=list)
    spells: list[MageSpell] = field(default_factory=list)
    equipment: list[Item | Weapon | Armor | Shield] = field(default_factory=list)

    warrior_base: int = 0
    rogue_base: int = 0
    mage_base: int = 0

    warrior_mod: int = 0
    rogue_mod: int = 0
    mage_mod: int = 0

    adv_taken: int = 0
    fate: int = 0
    fate_starting: int = 0
    armor_penalty: int = 0

    hit_points_max: int = 0
    mana_max: int = 0

    _hit_points: int = 0
    mana: int = 0
    base_defense: int = 0
    armor: int = 0
    armor_mod: int = 0
    hit_points_armor: int = 0

    attack_attribute: SkillAttribute = SkillAttribute.Warrior

    _massive_attack: bool = False

    @property
    def armor_worn_list(self) -> str:
        _ = ""
        for armor in self.armor_worn:
            _ += f"\n;## {armor}"
        return _

    @property
    def name(self) -> str:
        if self.location:
            return f"{self._name} <Room: {self.location}>"
        else:
            return f"{self._name}"

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def warrior(self) -> int:
        return self.warrior_base + self.warrior_mod

    @property
    def rogue(self) -> int:
        return self.rogue_base + self.rogue_mod

    @property
    def mage(self) -> int:
        return self.mage_base + self.mage_mod

    @property
    def massive_attack(self) -> bool:
        if not self._massive_attack:
            return False
        if self.has_talent("Massive Attack"):
            return True
        return False

    @massive_attack.setter
    def massive_attack(self, massive_attack: bool) -> None:
        self._massive_attack = massive_attack

    def has_talent(self, name: str) -> bool:
        for talent in self.talents:
            if name.lower() == talent.name.lower():
                return True
        return False

    @property
    def hp(self) -> int:
        return self.hit_points

    @hp.setter
    def hp(self, hp: int) -> None:
        self.hit_points = max(0, min(hp, self.hit_points_max))

    @property
    def defense(self) -> int:
        return self.base_defense + self.armor + self.armor_mod

    @property
    def is_alive(self) -> bool:
        return self.hit_points > 0

    @property
    def attack(self) -> int:
        bonus: int = 0
        if self.weapons:
            bonus = self.weapons[0].attack_bonus
        if self.hit_points < self.hit_points_max // 2:
            bonus -= 3
        if hasattr(self, "attack_attribute"):
            if self.attack_attribute == SkillAttribute.Warrior:
                return max(1, self.warrior + bonus)
            if self.attack_attribute == SkillAttribute.Mage:
                return max(1, self.mage + bonus)
            if self.attack_attribute == SkillAttribute.Rogue:
                return max(1, self.rogue + bonus)
        return max(1, self.warrior + bonus)

    @property
    def damage(self) -> str:
        damage: str = "1d2"
        if self.weapons:
            weapon: Weapon = self.weapons[0]
            damage = weapon.damage
        if self.hit_points < self.hit_points_max // 2:
            damage = f"({damage}) - 3"
        if self.massive_attack:
            damage = f"{damage} + {self.warrior}"
            self.massive_attack = False
        return damage

    @property
    def hit_points(self) -> int:
        return self._hit_points

    @hit_points.setter
    def hit_points(self, hit_points: int):
        self._hit_points = min(self.hit_points_max, hit_points)

    def hit_points_add(self, hit_points: int) -> int:
        self.hit_points = self.hit_points + hit_points
        return self.hit_points

    @property
    def weapon(self) -> Weapon:
        if not self.weapons:
            return Weapon("")
        return self.weapons[0]

    @property
    def hps(self) -> tuple[int, int]:
        return self.hit_points, self.hit_points_armor

    @hps.setter
    def hps(self, hit_points: tuple[int, int]) -> None:
        self.hit_points, self.hit_points_armor = hit_points

    def reset_pools(self) -> None:
        self.hit_points_max = 6 + self.warrior
        self.fate_starting = max(self.rogue, 1)
        self.mana_max = self.mage * 2

        self.hit_points = self.hit_points_max
        self.fate = self.fate_starting
        self.mana = self.mana_max - self.armor_penalty

        self.reset_defense()

    def reset_defense(self) -> int:
        self.base_defense = 4 + (self.warrior + self.rogue) // 2
        return self.defense

    def reset_armor_penalty(self) -> str:
        self.mana += self.armor_penalty
        if self.mana > self.mana_max:
            self.mana = self.mana_max
        self.armor_penalty = 0
        return f"Mana: {self.mana}/{self.mana_max}"

    def equip_weapon(self, new_weapon: Weapon) -> tuple[str, int, int]:
        for weapon in self.weapons.copy():
            if weapon.name.lower() == new_weapon.name.lower():
                self.weapons.remove(weapon)
        self.weapons.insert(0, new_weapon)
        return new_weapon.name, new_weapon.attack_bonus, new_weapon.damage_bonus

    def set_armor(self, defense: int, penalty: int) -> str:
        self.armor = defense
        self.armor_penalty = penalty
        self.mana = min(self.mana_max - self.armor_penalty, self.mana)
        self.hit_points_armor = 0  # 5 * self.armor
        return f"Total defense: {self.armor}, Mana Penalty: {self.armor_penalty}, Mana: {self.mana}"

    def equip_armor(self, armor: Armor) -> str:
        self.armor_worn.insert(0, armor)
        return self.set_armor(armor.defense, armor.armor_penalty)

    def print(self) -> None:
        print(f"Warrior: {self.warrior}, Adv. Taken: {self.adv_taken}")
        print(f"Rogue: {self.rogue}, Fate: {self.fate}")
        print(f"Mage: {self.mage}, Armor Penalty: {self.armor_penalty}")
        print()
        print(f"HP: {self.hit_points} ({self.hit_points_max})")
        print(f"Mana: {self.mana} ({self.mana_max})")
        print(f"Defense: {self.defense} = {self.base_defense=} | {self.armor=}")
        print()

        print("=== SKILLS ===")
        for skill in self.skills:
            print(f" - {skill}")
        print()

        print("=== TALENTS ===")
        for talent in self.talents:
            print(f" - {talent}")
        print()

        print("=== SPELLS ===")
        if not self.spells:
            print("None")
        for spell in self.spells:
            print(f" - {spell}")
        print()

        print("=== EQUIPMENT ===")
        if not self.equipment:
            print("None")
        for item in self.equipment:
            print(f" - {item}")
        print()

        print("=== WEAPONS ===")
        if not self.weapons:
            print("None")
        for item in self.weapons:
            print(f" - {item}")
        print()

        print("=== ARMOR ===")
        if not self.armor_worn:
            print("None")
        for item in self.armor_worn:
            print(f" - {item}")
        print()

    def attribute_level(self, skill: SkillAttribute) -> int:
        if skill == SkillAttribute.Rogue:
            return self.rogue
        elif skill == SkillAttribute.Mage:
            return self.mage
        elif skill == SkillAttribute.Warrior:
            return self.warrior

        return 0

    def skill_names(self) -> list[str]:
        skills: list[str] = list()
        for skill in self.skills:
            skills.append(skill.skill_name)
        return skills

    def cast(self, spell_name: str, mana_burn: bool = False) -> str:
        if not self.spells:
            return "No spells."
        for spell in self.spells:
            if spell.name.lower() == spell_name.lower():
                if self.mana < spell.mana_cost:
                    return f"Not enough mana ({self.mana}) for {spell.name} ({spell.mana_cost})"
                roll: int = dice.roll(f"1d6 + {self.mage}")
                if roll < spell.difficulty.value:
                    return f"Cast failed. {roll} < {spell.difficulty.name} {spell.difficulty.value}"
                self.mana -= spell.mana_cost
                return f"Cast succeeded. {spell.name}: {spell.description}"
        return "That spell is not available."

    def spell_list(self, all: bool = False) -> list[str]:
        spells: list[str] = list()
        for spell in self.spells:
            if not all and spell.mana_cost > self.mana:
                continue
            spells.append(f"{spell.name}: {spell.difficulty.name}, Mana: {spell.mana_cost:,}")
        return spells

    def spell_add(self, name: str) -> MageSpell:
        new_spell: MageSpell = MageSpellList.spell_by_name(name)
        for spell in self.spells:
            if name.lower() == spell.name.lower():
                return spell
        self.spells.append(new_spell)
        return new_spell

    def attack_opponent(self, opponent, bonus_roll: str = "") -> bool:
        bonus: int = 0
        if bonus_roll:
            bonus = dice.roll(f"{bonus_roll}")
        attack_attribute, defense = self.attack + bonus, opponent.defense
        check: int = roll(f"1d6x+{attack_attribute}")
        return True if check >= defense else False

    def damage_opponent(self, opponent, extra: str = "") -> int:
        opponent: CharacterSheet
        return opponent.take_damage_roll(self.damage, extra)

    def take_damage_from(self, opponent, extra_damage: str = "") -> int:
        opponent: CharacterSheet
        return self.take_damage_roll(opponent.damage, extra_damage)

    def take_damage_roll(self, die: str = "1d6x", extra_damage: str = "") -> int:
        damage: int = roll(f"{die} + {extra_damage}") if extra_damage else roll(f"{die}")
        self.hit_points -= damage
        if self.hit_points < 0:
            self.hit_points = 0
        return self.hit_points

    def moral_check(self, bonus: int = 0) -> str:
        return dl_check("Routine", self.warrior + bonus)

    def run_combat4(self, side_b: list["CharacterSheet"],  #
                    max_opponents: int = 3  #
                    ) -> list[str]:
        logs: list[list[str]] = list()
        for _ in range(4):
            copy_self = copy_of(self)
            copy_side_b = copy_of(side_b)
            logs.append(copy_self.run_combat(copy_side_b, max_opponents=max_opponents))
        logs.sort(key=len)
        return logs[0]

    def run_combat(self,  #
                   side_b: list["CharacterSheet"],  #
                   max_opponents: int = 1) -> list[str]:

        combat_log: list[str] = list()
        side_a = [self]

        npc_1: CharacterSheet = side_b[0]
        have_initiative: bool = initiative_check(self.rogue, npc_1.rogue)

        combat_log.append("")
        if have_initiative:
            combat_log.append("; PC party has initiative")
        else:
            combat_log.append("; NPC party has initiative")

        pc_hp: int = 0
        for pc in side_a:
            pc_hp += pc.hit_points

        npc_hp: int = 0
        for npc in side_b:
            npc_hp += npc.hit_points

        while True:
            if have_initiative:
                # combat_log.append("")
                for pc in side_a:
                    if not pc.is_alive:
                        continue
                    npc: CharacterSheet | None = None
                    for npc in side_b:
                        if not npc.is_alive:
                            continue
                        break
                    if not npc or not npc.is_alive:
                        continue
                    # combat_log.append(f"; {pc.name} attacks {npc.name}")
                    if pc.attack_opponent(npc):
                        if pc.massive_attack:
                            combat_log.append(f"; {pc.name} uses talent massive attack")
                        hp: int = npc.hit_points
                        npc.hit_points = pc.damage_opponent(npc)
                        if npc.hit_points < 1:
                            combat_log.append(f"; {pc.name} hits for {hp - npc.hit_points} points and {npc.name} dies")
                        else:
                            combat_log.append(f"; {pc.name} hits {npc.name} for {hp - npc.hit_points} points of damage")
                    else:
                        pass  # combat_log.append(f"; {pc.name} misses {npc.name}")
            else:
                counter: int = 0
                random.shuffle(side_b)
                for npc in side_b:
                    if not npc.is_alive:
                        continue
                    counter += 1
                    if counter > max_opponents:
                        break
                    pc: CharacterSheet | None = None
                    for pc in side_a:
                        if not pc.is_alive:
                            continue
                        break
                    if not pc or not pc.is_alive:
                        continue
                    # combat_log.append(f"; {npc.name} attacks {pc.name}")
                    if npc.attack_opponent(pc):
                        hp: int = pc.hit_points
                        pc.hit_points = npc.damage_opponent(pc)
                        if pc.hit_points < 1:
                            combat_log.append(f"; {npc.name} hits for {hp - pc.hit_points} points and kills {pc.name}")
                        else:
                            combat_log.append(f"; {npc.name} hits {pc.name} for {hp - pc.hit_points} points of damage")
                    else:
                        pass  # combat_log.append(f"; {npc.name} misses {pc.name}")

            new_pc_hp: int = 0
            for pc in side_a:
                new_pc_hp += pc.hit_points

            new_npc_hp: int = 0
            for npc in side_b:
                new_npc_hp += npc.hit_points

            if new_npc_hp < 1:
                combat_log.append("")
                combat_log.append(";NPC party perished")
                break

            if new_pc_hp < 1:
                combat_log.append("")
                combat_log.append(";PC party perished")
                break

            if new_pc_hp < pc_hp // 2:
                # combat_log.append("")
                # combat_log.append(f";PC party low on HP")  # break
                pass

            have_initiative = not have_initiative

        combat_log.append("")
        for npc in side_b:
            combat_log.append(f";{npc.name} hit points = {npc.hit_points}")
        combat_log.append("")
        for pc in side_a:
            combat_log.append(f";{pc.name} hit points = {pc.hit_points}")
        if pc.hit_points > 0:
            combat_log.append(";win")
        else:
            combat_log.append(";lose")
        return combat_log

    @property
    def equipment_list(self) -> str:
        _ = ""
        for item in self.equipment:
            _ += f"\n;## {item.name}\n"
        return _
