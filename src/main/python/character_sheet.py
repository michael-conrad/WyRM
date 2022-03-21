import random
import textwrap
from dataclasses import dataclass
from dataclasses import field

import dice
import jsonpickle

import gamebook_core
from equipment import Armor
from equipment import Item
from equipment import Money
from equipment import Shield
from equipment import Weapon
from gb_utils import dl_check
from gb_utils import initiative_check
from gb_utils import intervention
from gb_utils import roll
from mana import MageSpell
from mana import MageSpellList
from skills import CharacterSkill
from skills import SkillAttribute
from talents import CharacterTalent


def copy_of(o) -> any:
    return jsonpickle.decode(jsonpickle.encode(o))


@dataclass(slots=True)
class CharacterSheet(gamebook_core.AbstractCharacter):
    xp: int = 0
    _name: str = ""
    location: str = ""
    description: str = ""
    weapons: list[Weapon] = field(default_factory=list)
    armor_worn: list[Armor] = field(default_factory=list)
    skills: list[CharacterSkill] = field(default_factory=list)
    talents: list[CharacterTalent] = field(default_factory=list)
    spells: list[MageSpell] = field(default_factory=list)
    equipment: list[Item | Weapon | Armor | Shield | Money] = field(default_factory=list)

    warrior_base: int = 0
    rogue_base: int = 0
    mage_base: int = 0

    _warrior_mod: int = 0
    _rogue_mod: int = 0
    _mage_mod: int = 0

    adv_taken: int = 0
    fate: int = 0
    fate_starting: int = 0
    armor_penalty: int = 0

    hit_points_max: int = 0
    mana_max: int = 0

    _hit_points: int = 0
    mana: int = 0
    base_defense: int = 0
    _defense_mod: int = 0
    armor: int = 0
    armor_mod: int = 0
    hit_points_armor: int = 0

    attack_attribute: SkillAttribute = SkillAttribute.Warrior

    _massive_attack: bool = False

    _saved_inv: list[str] = field(default_factory=list)

    @property
    def darkvision(self) -> bool:
        for item in self.armor_worn:
            name = item.name.lower()
            if "darkvision" in name:
                return True
            if "dark vision" in name:
                return True
        for item in self.weapons:
            name = item.name.lower()
            if "darkvision" in name:
                return True
            if "dark vision" in name:
                return True
        return False

    def save_inv_list(self) -> None:
        for item in self.armor_worn:
            self._saved_inv.append(item.base_name)
        for item in self.weapons:
            self._saved_inv.append(item.base_name)
        for item in self.equipment:
            self._saved_inv.append(item.base_name)

    @property
    def found_items(self) -> list[str] | None:
        _ = list()
        for item in self.armor_worn:
            if item.base_name not in self._saved_inv:
                _.append(f"* {item.base_name}")
        for item in self.weapons:
            if item.base_name not in self._saved_inv:
                _.append(f"* {item.base_name}")
        for item in self.equipment:
            if item.base_name not in self._saved_inv:
                _.append(f"* {item.base_name}")
        if not _:
            return None
        return _

    @property
    def starting_items(self) -> str:
        _ = ""
        for item in self._saved_inv:
            _ += f"\n;## {item}"
        return _

    @property
    def warrior_mod(self) -> int:
        return self._warrior_mod

    @warrior_mod.setter
    def warrior_mod(self, mod: int) -> None:
        self._warrior_mod = mod
        self.reset_defense()

    @property
    def rogue_mod(self) -> int:
        return self._rogue_mod

    @rogue_mod.setter
    def rogue_mod(self, mod: int) -> None:
        self._rogue_mod = mod
        self.reset_defense()

    @property
    def mage_mod(self) -> int:
        return self._mage_mod

    @mage_mod.setter
    def mage_mod(self, mod: int) -> None:
        self._mage_mod = mod
        self.reset_mana_max()

    @property
    def is_full_health(self) -> str:
        at_full_health: bool = self.hp >= self.hit_points_max
        if at_full_health:
            return f"At full health. {self.hp}/{self.hit_points_max}"
        return f"Not at full health. {self.hp}/{self.hit_points_max}"

    @property
    def list_armor_equipped(self) -> str:
        _ = ""
        for armor in self.armor_worn:
            _ += f"* {armor.base_name}\n"
        return _

    def add_item(self, item: Shield | Armor | Item | Weapon | Money | str) -> None:
        if isinstance(item, str):
            item = Item(item)
        self.equipment.append(item)

    def add_items(self, items: list[Shield | Armor | Item | Weapon | Money | str]) -> None:
        if not isinstance(items, list):
            items = [items]
        item: Shield | Armor | Item | Weapon | Money | str
        for item in items:
            self.add_item(item)

    @property
    def name(self) -> str:
        if self.location:
            return f"{self._name} (HP: {self.hp}, XP: {self.xp}) <Room: {self.location}>"
        else:
            return f"{self._name} (HP: {self.hp}, XP: {self.xp})"

    @name.setter
    def name(self, name: str) -> None:
        if " (#" in self._name and not " (#" in name:
            self._name = name + self._name[self._name.index(" (#"):]
        else:
            self._name = name

    @property
    def base_name(self) -> str:
        return self._name

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
        damage: str = "1d2x"
        if self.weapons:
            weapon: Weapon = self.weapons[0]
            damage = weapon.damage
        if self.hit_points < self.hit_points_max // 2:
            damage = f"({damage})-3"
        if self.massive_attack:
            damage = f"{damage}{self.warrior:+}"
            self.massive_attack = False
        return damage

    @property
    def hit_points(self) -> int:
        return self._hit_points

    @hit_points.setter
    def hit_points(self, hit_points: int):
        self._hit_points = min(self.hit_points_max, hit_points)

    def hp_add(self, hp: int) -> int:
        self.hp = self.hp + hp
        return self.hp

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

    def drop(self, name: str) -> Weapon | Armor | Shield | Item | None:
        name = name.lower()
        for wpn in self.weapons:
            if name in wpn.name.lower():
                self.weapons.remove(wpn)
                return wpn
            pass
        for arm in self.armor_worn:
            if name in arm.name.lower():
                self.armor_worn.remove(arm)
                return arm
        for item in self.equipment:
            if name in item.name.lower():
                self.equipment.remove(item)
                return item
        return Item("NOT FOUND")

    def item(self, name: str) -> Weapon | Armor | Shield | Item | None:
        name = name.lower()
        for wpn in self.weapons:
            if name in wpn.name.lower():
                return wpn
            pass
        for arm in self.armor_worn:
            if name in arm.name.lower():
                return arm
        for item in self.equipment:
            if name in item.name.lower():
                return item
        return Item("NOT FOUND")

    def has_item(self, name: str) -> bool:
        name = name.lower()
        for wpn in self.weapons:
            if name in wpn.name.lower():
                return True
            pass
        for arm in self.armor_worn:
            if name in arm.name.lower():
                return True
        for item in self.equipment:
            if name in item.name.lower():
                return True
        return False

    def reset_hp_max(self) -> int:
        self.hit_points_max = 6 + self.warrior
        self.hit_points = min(self.hit_points, self.hit_points_max)
        return self.hit_points_max

    def reset_mana_max(self) -> int:
        self.mana_max = self.mage * 2
        self.mana = min(self.mana_max - self.armor_penalty, self.mana)
        return self.mana_max

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

    def equip_weapon(self, new_weapon: Weapon):
        for weapon in self.weapons.copy():
            if weapon.name.lower() == new_weapon.name.lower():
                self.weapons.remove(weapon)
        self.weapons.insert(0, new_weapon)
        return None

    def set_armor(self, defense: int, penalty: int) -> str:
        self.armor = defense
        self.armor_penalty = penalty
        self.mana = min(self.mana_max - self.armor_penalty, self.mana)
        self.hit_points_armor = 0  # 5 * self.armor
        return f"Total defense: {self.defense}, Mana Penalty: {self.armor_penalty}, Mana: {self.mana}"

    def equip_armor(self, armor: Armor) -> None:
        self.armor_worn.insert(0, armor)
        self.set_armor(armor.defense, armor.armor_penalty)

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

    def cast(self, spell_name: str, mana_burn: bool = False) -> list[str]:
        if not self.spells:
            return list("; No spells.")
        spell_name = spell_name.lower()
        for spell in self.spells:
            if spell.name.lower().startswith(spell_name):
                if self.mana < spell.mana_cost:
                    return [f"; Not enough mana ({self.mana}) for {spell.name} ({spell.mana_cost})"]
                check: int = dice.roll(f"1d6 + {self.mage}")
                if check < spell.difficulty.value:
                    return [f"; Cast failed. {check} < {spell.difficulty.name} {spell.difficulty.value}"]
                result: list[str] = list()
                self.mana -= spell.mana_cost
                pc_id: str = f"player" if "Player" in self.name else f"room.npc(\"{self._name}\")"
                result.append(f"; Cast succeeded. {spell.name}: {spell.description}");
                if spell.macro:
                    for macro in spell.macro:
                        result.append(macro.replace("pc_id", f"{pc_id}"))
                else:
                    result.append(f"@{pc_id}.mana: {pc_id}.mana - {spell.mana_cost}")
                return result
        return ["; That spell is not available."]

    @property
    def spell_list(self) -> str:
        spells: str = ""
        for spell in self.spells:
            if spell.mana_cost > self.mana:
                continue
            spells += f"* {spell.name}: {spell.difficulty.name}, Mana: {spell.mana_cost:,}\n"
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
        if damage < 1:
            damage = 1
        self.hit_points -= damage
        if self.hit_points < 0:
            self.hit_points = 0
        return self.hit_points

    def moral_check(self, bonus: int = 0) -> str:
        return dl_check("Routine", self.warrior + bonus)

    def run_combat4(self, side_b: list["CharacterSheet"],  #
                    max_opponents: int = 3  #
                    ) -> list[str]:
        if not isinstance(side_b, list):
            side_b = [side_b]
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

        if isinstance(side_b, list):
            pass
        else:
            side_b = [side_b]

        combat_log: list[str] = list()
        side_a = [self]

        for c in side_a:
            combat_log.append(f"; {c.name} {c.weapon}")
        for c in side_b:
            combat_log.append(f"; {c.name} {c.weapon}")
        combat_log.append("")

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
                    if pc.attack_opponent(npc):
                        var: str = "_"
                        if "Player" in pc._name:
                            var = "player"
                        else:
                            var = f"room.npc(\"{pc._name}\")"
                        if pc.massive_attack:
                            combat_log.append(f"; {pc._name} uses talent massive attack")
                            combat_log[-1] = f"!{var}.massive_attack=False # " + combat_log[-1]
                        hp: int = npc.hit_points
                        npc.hit_points = pc.damage_opponent(npc)
                        if npc.hit_points < 1:
                            combat_log.append(
                                    f"; {pc._name} hits for {hp - npc.hit_points} points and {npc._name} dies")
                        else:
                            combat_log.append(
                                    f"; {pc._name} hits {npc.name} for {hp - npc.hit_points} points of damage")
                        if "Player" in npc._name:
                            var = "player"
                        else:
                            var = f"room.npc(\"{npc._name}\")"
                        combat_log[-1] = f"!{var}.hp={npc.hit_points} # " + combat_log[-1]
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
                    if npc.attack_opponent(pc):
                        var: str = "_"
                        if "Player" in npc._name:
                            var = "player"
                        else:
                            var = f"room.npc(\"{npc._name}\")"
                        hp: int = pc.hit_points
                        pc.hit_points = npc.damage_opponent(pc)
                        if pc.hit_points < 1:
                            combat_log.append(
                                    f"; {npc._name} hits for {hp - pc.hit_points} points and kills {pc._name}")
                        else:
                            combat_log.append(
                                    f"; {npc._name} hits {pc._name} for {hp - pc.hit_points} points of damage")
                        var: str = "_"
                        if "Player" in pc._name:
                            var = "player"
                        else:
                            var = f"room.npc(\"{pc._name}\")"
                        combat_log[-1] = f"!{var}.hp = {pc.hit_points} # " + combat_log[-1]

            new_pc_hp: int = 0
            for pc in side_a:
                new_pc_hp += pc.hit_points

            new_npc_hp: int = 0
            for npc in side_b:
                new_npc_hp += npc.hit_points

            if not new_npc_hp:
                break

            if not new_pc_hp:
                break

            have_initiative = not have_initiative

        combat_log.append("")
        side_b.sort(key=lambda x: x.name)
        for npc in side_b:
            if npc.is_alive:
                combat_log.append(f"; {npc._name}")
            else:
                combat_log.append(f"; DEAD: {npc._name}")
        side_a.sort(key=lambda x: x.name)
        for pc in side_a:
            if pc.is_alive:
                combat_log.append(f"; {pc._name}")
            else:
                combat_log.append(f"; DEAD: {pc._name}")
        if not new_pc_hp and self.fate:
            self.fate -= 1
            combat_log.append(f"@player.fate: {self.fate}")
            if self.fate:
                combat_log.append("")
                combat_log.append(f"FATE - 1. FATE POINTS REMAINING: {self.fate}")
                combat_log.append("")
                combat_log.append(f"; {textwrap.fill(intervention(), 80).strip()}".replace("\n", "\n; "))
            else:
                combat_log.append("")
                combat_log.append(f"FATE - 1. NO FATE POINTS REMAINING.")
                combat_log.append("")
                combat_log.append(f"; {textwrap.fill(intervention(), 80).strip()}".replace("\n", "\n; "))
        return combat_log

    def run_combat_round(self,  #
                         side_b: list["CharacterSheet"],  #
                         max_opponents: int = 3,  #
                         opponents_have_initiative: None | bool = None) -> list[str]:

        combat_log: list[str] = list()
        side_a = [self]
        hp_to_report: dict[str, int] = dict()

        npc_1: CharacterSheet
        if isinstance(side_b, list):
            pass
        else:
            side_b = [side_b]

        npc_1 = side_b[0]

        have_initiative: bool
        if opponents_have_initiative is not None:
            have_initiative = not opponents_have_initiative
        else:
            have_initiative = initiative_check(self.rogue, npc_1.rogue)

        pc_hp: int = 0
        for pc in side_a:
            pc_hp += pc.hit_points

        npc_hp: int = 0
        for npc in side_b:
            npc_hp += npc.hit_points

        if have_initiative:
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
                var: str = "_"
                if "Player" in pc._name:
                    var = "player"
                else:
                    var = f"room.npc(\"{pc._name}\")"
                if pc.massive_attack:
                    combat_log.append(f"; {pc._name} uses talent massive attack")
                    combat_log[-1] = f"!{var}.massive_attack=False # " + combat_log[-1]
                hp: int = npc.hit_points
                npc.hit_points = pc.damage_opponent(npc)
                if npc.hit_points < 1:
                    combat_log.append(f"; {pc._name} hits for {hp - npc.hit_points} points and {npc._name} dies")
                else:
                    combat_log.append(f"; {pc._name} hits {npc.name} for {hp - npc.hit_points} points of damage")
                if "Player" in npc._name:
                    var = "player"
                else:
                    var = f"room.npc(\"{npc._name}\")"
                combat_log[-1] = f"!{var}.hp={npc.hit_points} # " + combat_log[-1]
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
                if npc.attack_opponent(pc):
                    var: str = "_"
                    if "Player" in npc._name:
                        var = "player"
                    else:
                        var = f"room.npc(\"{npc._name}\")"
                    hp: int = pc.hit_points
                    pc.hit_points = npc.damage_opponent(pc)
                    if pc.hit_points < 1:
                        combat_log.append(f"; {npc._name} hits for {hp - pc.hit_points} points and kills {pc._name}")
                    else:
                        combat_log.append(f"; {npc._name} hits {pc._name} for {hp - pc.hit_points} points of damage")
                    var: str = "_"
                    if "Player" in pc._name:
                        var = "player"
                    else:
                        var = f"room.npc(\"{pc._name}\")"
                    combat_log[-1] = f"!{var}.hp = {pc.hit_points} # " + combat_log[-1]
        return combat_log

    @property
    def list_gear(self) -> str:
        _ = list()
        item: Item
        counts: dict[str, int] = dict()
        for item in self.equipment:
            if item.name not in counts:
                counts[item.name] = 0
            counts[item.name] += 1
        for item in self.equipment:
            if item.name not in counts:
                continue
            qty = counts[item.name]
            del counts[item.name]
            if qty>1:
                _.append(f"* {item.name} ({qty} each)")
            else:
                _.append(f"* {item.name}")
        _.sort()
        return "\n".join(_)

    @property
    def list_money(self) -> str:
        self.combine_monies()
        _ = ""
        for item in self.equipment:
            if isinstance(item, Money) and item.cp:
                _ += f"* {item.name}\n"
        return _

    def combine_monies(self) -> list[Money]:
        new_list: list[Money] = list()
        for item in self.equipment.copy():
            if isinstance(item, Money):
                new_list.append(item)
                self.equipment.remove(item)
        if new_list:
            new_list = Money.money_combine(new_list)
            self.equipment.extend(new_list)
        return new_list

    def spend_money(self, cost: Money) -> None:
        cp = 0
        for kind in ["C", "S", "E", "G", "P"]:
            for item in [*self.equipment]:
                if isinstance(item, Money):
                    cp += item.cp
                    self.equipment.remove(item)
                    if cp >= cost.cp:
                        break
        cp = max(cp - cost.cp, 0)
        if cp:
            m: Money = Money().as_kind("C").at_qty(cp)
            for change in Money.money_changer([m]):
                self.add_item(change)
        self.combine_monies()

    @property
    def money(self):
        cp: int = 0
        for item in self.equipment:
            if isinstance(item, Money):
                cp += item.cp
        m = Money(_kind="C", _qty=cp)
        return m

    @property
    def list_armor(self) -> str:
        _ = ""
        for item in self.armor_worn:
            if isinstance(item, Armor):
                _ += f"* {item.name}. Defense: {item.defense}. Mana penalty: -{item.armor_penalty}.\n"
        return _

    @property
    def list_weapons(self) -> str:
        _ = ""
        for item in self.weapons:
            if isinstance(item, Weapon):
                _ += f"* {item.name}. Damage: {item.damage}.\n"
        return _
