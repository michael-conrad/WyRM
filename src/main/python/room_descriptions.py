import random
import textwrap
from dataclasses import dataclass
from dataclasses import field

import jsonpickle

from character_sheet import CharacterSheet
from equipment import Armor
from equipment import Item
from equipment import Weapon
from gb_utils import loot
from mob_combat import MobUnit


@dataclass(slots=True)
class RoomDescription:
    name: str = ""
    _facing: str = "facing"
    _desc1: str = ""
    _desc2: str = ""
    notes: str = ""
    items: list[Item | Armor | Weapon | CharacterSheet] = field(default_factory=list)
    new_visit: bool = True
    views: int = 0
    _complete: bool = False
    last_combat: list[str] = field(default_factory=list)
    _directions: dict[str, str] = field(default_factory=dict)

    @property
    def directions(self) -> dict[str, str]:
        return self._directions

    @directions.setter
    def directions(self, directions: dict[str, str]) -> None:
        self._directions = directions

    def kill_npcs(self, name: str | None = None) -> str:
        _ = ""
        for item in self.items:
            if isinstance(item, CharacterSheet):
                if name is None or name in item.name:
                    item.hp = 0
                    _ += f"\n;## {item.name}"
        return _

    def go(self, direction: str) -> list[str] | None | str:
        direction=direction.lower()
        if direction == "back":
            direction = "rear"
        if direction == "forwards" or direction == "forward":
            direction = "front"
        un_relative: dict[str, dict[str]] = dict()
        un_relative["n"] = {"front": "n", "right": "e", "rear": "s", "left": "w"}
        un_relative["e"] = {"front": "e", "right": "s", "rear": "w", "left": "n"}
        un_relative["s"] = {"front": "s", "right": "w", "rear": "n", "left": "e"}
        un_relative["w"] = {"front": "w", "right": "n", "rear": "e", "left": "s"}
        if self.facing in un_relative:
            mapping = un_relative[self.facing]
            if direction in mapping:
                direction = mapping[direction]
        result: list[str] = list()
        if direction not in self.directions and direction in self.directions.values():
            for item in self.directions.items():
                if item[1].lower() == direction.lower():
                    direction = item[0]
                    break
        if direction not in self.directions:
            return None
        result.append("")
        result.append(f"!facing=\"{direction}\"")
        result.append(f"!location=\"{self.directions[direction]}\"")
        result.append(f"!room=rooms(location).with_facing(facing)")
        result.append(f"!room")
        self.facing = direction
        new_room = rooms(self.directions[direction]).with_facing(direction)
        result.append(str(new_room))
        return result

    @property
    def desc1(self) -> str:
        return self.fix_directions(self._desc1)

    @property
    def desc2(self) -> str:
        return self.fix_directions(self._desc2)

    def set_desc1(self, desc: str) -> None:
        self._desc1 = desc

    def set_desc2(self, desc: str) -> None:
        self._desc2 = desc

    def add_desc(self, desc: str) -> None:
        desc = desc.strip()
        if not desc:
            return
        self._desc1 += f" {desc}"
        self._desc2 += f" {desc}"

    def fix_directions(self, desc: str) -> str:
        if self.facing.lower() == "n":
            desc = desc.replace("/N/", "in front of you")
            desc = desc.replace("/E/", "to your right")
            desc = desc.replace("/S/", "behind you")
            desc = desc.replace("/W/", "to your left")

        if self.facing.lower() == "e":
            desc = desc.replace("/E/", "in front of you")
            desc = desc.replace("/S/", "to your right")
            desc = desc.replace("/W/", "behind you")
            desc = desc.replace("/N/", "to your left")

        if self.facing.lower() == "s":
            desc = desc.replace("/S/", "in front of you")
            desc = desc.replace("/W/", "to your right")
            desc = desc.replace("/N/", "behind you")
            desc = desc.replace("/E/", "to your left")

        if self.facing.lower() == "w":
            desc = desc.replace("/W/", "in front of you")
            desc = desc.replace("/N/", "to your right")
            desc = desc.replace("/E/", "behind you")
            desc = desc.replace("/S/", "to your left")

        return desc

    @property
    def facing(self) -> str:
        return self._facing

    @facing.setter
    def facing(self, new_facing: str) -> None:
        self._facing = new_facing

    def with_facing(self, new_facing: str) -> "RoomDescription":
        self._facing = new_facing
        return self

    @property
    def complete(self) -> bool:
        return not self.new_visit and self._complete

    @complete.setter
    def complete(self, complete: bool) -> None:
        self._complete = complete

    def npc_group(self, substring: str) -> list[CharacterSheet]:
        result: list[CharacterSheet] = list()
        for x in self.items:
            if isinstance(x, CharacterSheet):
                if substring.lower() in x.name.lower():
                    result.append(x)
        return result

    def mob_group(self, substring: str) -> MobUnit:
        m = MobUnit()
        m.units = self.npc_group(substring)
        return m

    @property
    def mob(self) -> MobUnit:
        m = MobUnit()
        m.units = self.npcs
        return m

    @property
    def mob_alive(self) -> MobUnit:
        m = MobUnit()
        units: list[CharacterSheet] = list()
        for unit in self.npcs:
            if unit.is_alive:
                units.append(unit)
        m.units = units
        return m

    @property
    def mob_dead(self) -> MobUnit:
        m = MobUnit()
        units: list[CharacterSheet] = list()
        for unit in self.npcs:
            if not unit.is_alive:
                units.append(unit)
        m.units = units
        return m

    def mob_combat(self, substring_a: str, substring_b: str) -> list[str]:
        m1: MobUnit = self.mob_group(substring_a)
        m2: MobUnit = self.mob_group(substring_b)
        for unit in m1.units:
            if unit in m2.units:
                m2.units.remove(unit)
        self.last_combat = m1.combat(m2)
        return self.last_combat

    def add_items(self, items: list[Item | Armor | Weapon | CharacterSheet | str]) -> list[str]:
        result: list[str] = list()
        result.append(f";;; Items: {len(items)}")
        for item in items:
            pickled = jsonpickle.encode(item, use_base85=True, indent=None).replace("\\", "\\\\").replace("'", "\\'")
            pickled = f"'{pickled}'"
            result.append(f"!room.add_item(unpickle({pickled}))")
            self.add_item(item)
        result.append("!room.inv")
        result.append(self.inv)
        return result

    def add_item(self, item: Item | Armor | Weapon | CharacterSheet | str, quiet: bool = True) -> str | None:
        if isinstance(item, str):
            item = Item(item)
        self.items.append(item)
        if quiet:
            return None
        idx: int = self.items.index(item) + 1
        _: str = f"\n;## [{idx}] {item.name}"
        if isinstance(item, Armor):
            return f"\n;## [{idx}] Armor: {item.name.strip()}"
        if isinstance(item, Weapon):
            return f"\n;## [{idx}] Weapon: {item.name.strip()}"
        if isinstance(item, CharacterSheet):
            return f"\n;## [{idx}] {item.name.strip()}"
        return f"\n;## [{idx}] {item.name.strip()}"

    def pop_item(self, name: str) -> Item | Armor | Weapon | CharacterSheet | None:
        for _, x in enumerate([x.name for x in self.items]):
            if x.lower().startswith(name.lower()):
                return self.items.pop(_)
            if f"({name.lower()})" in x.lower():
                return self.items.pop(_)
            if f"(#{name.lower()})" in x.lower():
                return self.items.pop(_)
            if f"{name.lower()}" in x.lower():
                return self.items.pop(_)
        return None

    def pop_items(self, name: str) -> list[Item | Armor | Weapon | CharacterSheet]:
        items: list[Item | Armor | Weapon | CharacterSheet] = list()
        name = name.lower()
        for item in self.items.copy():
            item_name = item.name.lower()
            if name in item_name:
                self.items.remove(item)
                items.append(item)
        return items

    def remove_items(self, name: str) -> str:
        items: str = ""
        name = name.lower()
        for item in self.items.copy():
            item_name = item.name.lower()
            if name in item_name:
                self.items.remove(item)
                items += f"\n;## Removed {item.name}"
        return items

    def get_item(self, name: str) -> Item | Armor | Weapon | CharacterSheet | None:
        return self.item(name)

    def item(self, name: str) -> Item | Armor | Weapon | CharacterSheet | None:
        for _, x in enumerate([x.name for x in self.items]):
            if x.lower().startswith(name.lower()):
                return self.items[_]
            if f"({name.lower()})" in x.lower():
                return self.items[_]
            if f"(#{name.lower()})" in x.lower():
                return self.items[_]
            if f"{name.lower()}" in x.lower():
                return self.items[_]

    def __str__(self):
        self.views += 1
        desc = self.desc1.strip() if self.new_visit else self.desc2.strip()
        if not desc:
            desc = self.desc1.strip()
        self.new_visit = False
        _: str = ""
        for line in textwrap.wrap(desc, tabsize=4):
            _ += f"\n;## {line}"
        desc = _

        result: str = f"\n;## ROOM: {self.name} ({self.views:,})"
        if desc.strip():
            result += "\n"
            result += desc.strip() + "\n"
        if self.items:
            result += "\n"
            result += self.inv
        if self.notes:
            result += "\n"
            notes: str = textwrap.fill(self.notes, 80).replace("\n", "\n;## ")
            result += f"\n;## {notes}"
        if self.directions:
            result += "\n"
            directions = [k for k in self.directions.keys()]
            directions.sort()
            for direction in directions:
                relative: str = self.fix_directions(f"/{direction.upper()}/")
                room_name = self.directions[direction]
                if rooms(room_name).complete:
                    room_name += " ***"
                if relative.startswith("/"):
                    result += f"\n;## {direction}: {room_name}"
                else:
                    result += f"\n;## {relative} [{direction.upper()}]: {room_name}"
        return result

    @property
    def info(self) -> str:
        desc = self.desc2.strip()
        if not desc:
            desc = self.desc1.strip()
        _: str = ""
        for line in textwrap.wrap(desc, 80):
            _ += f"\n;## {line}"
        desc = _

        result: str = f"\n;## ROOM: {self.name} (Visited: {not self.new_visit})"
        if desc.strip():
            result += desc
        if self.items:
            result += "\n;##"
            result += self.item_list
        if self.notes:
            result += f"\n;## {self.notes}"

        if self.directions:
            result += f"\n;## "
            directions = [k for k in self.directions.keys()]
            directions.sort()
            for direction in directions:
                relative: str = self.fix_directions(f"/{direction.upper()}/")
                room_name = self.directions[direction]
                if rooms(room_name).complete:
                    room_name += "*"
                if relative.startswith("/"):
                    result += f" {direction}→{room_name}"
                else:
                    result += f" {relative}→{room_name}"
        return result

    @property
    def info_directions(self) -> str:
        result:str = ""
        if self.directions:
            result += f"\n;## "
            directions = [k for k in self.directions.keys()]
            directions.sort()
            for direction in directions:
                relative: str = self.fix_directions(f"/{direction.upper()}/")
                room_name = self.directions[direction]
                if rooms(room_name).complete:
                    room_name += "*"
                if relative.startswith("/"):
                    result += f" {direction}→{room_name}"
                else:
                    result += f" {relative}→{room_name}"
        return result

    @property
    def inv(self) -> str:
        result = ""
        if self.items:
            for item in self.items:
                idx: int = self.items.index(item) + 1
                result += f"\n;## [{idx}] "
                if isinstance(item, CharacterSheet):
                    if item.hp < 1:
                        result += "DEAD "
                result += f"{item.name}"
        return result

    @property
    def item_list(self) -> str:
        return self.inv

    @property
    def npcs(self) -> list[CharacterSheet]:
        result: list = list()
        if self.items:
            for item in self.items:
                if isinstance(item, CharacterSheet):
                    if item.is_alive:
                        result.append(item)
            for item in self.items:
                if isinstance(item, CharacterSheet):
                    if not item.is_alive:
                        result.append(item)
        return result

    def npc_sublist(self, identifiers: list[str]) -> list[CharacterSheet]:
        result: list[CharacterSheet] = list()
        for _ in identifiers:
            npc = self.get_item(_)
            if npc:
                if isinstance(npc, CharacterSheet):
                    result.append(npc)
        return result

    def npc(self, identifier: str) -> CharacterSheet | None:
        if isinstance(identifier, int):
            identifier -= 1
            if identifier < 0:
                return None
            if len(self.items) > identifier and isinstance(self.items[identifier], CharacterSheet):
                return self.items[identifier]
        identifier = str(identifier).lower()
        for item in self.items:
            name = item.name.lower()
            if isinstance(item, CharacterSheet):
                if f"(#{identifier})" in name:
                    return item
                if f"({identifier})" in name:
                    return item
                if f"{identifier}" in name:
                    return item
        return None

    @property
    def npc_list(self) -> str:
        result: str = ""
        if self.items:
            for item in self.items:
                if isinstance(item, CharacterSheet):
                    if item.hp < 1:
                        result += f"\n;## {item.name} (DEAD)"
                    else:
                        result += f"\n;## {item.name}"
        return result


@dataclass(slots=True)
class Rooms:
    rooms: dict[str, RoomDescription] = field(default_factory=dict)

    def room(self, name: str) -> RoomDescription:
        if name not in self.rooms:
            this_room: RoomDescription = RoomDescription(name=f"{name}")
            this_room._desc1 = f"ROOM {name} NOT FOUND!"
            self.rooms[name] = this_room
        room = self.rooms[name]
        return room

    def save_rooms(self) -> str:
        pickled: str = jsonpickle.encode(self.rooms)
        pickled = pickled.replace("\\", "\\\\").replace("\"", "\\\"")
        return f"\"{pickled}\""

    def restore_rooms(self, pickled: str) -> "Rooms":
        self.rooms = jsonpickle.decode(pickled)
        return self

    @classmethod
    def move_all_items(cls, from_room: RoomDescription | str, dest_room: RoomDescription | str) -> str:
        global _rooms
        _: str = ""
        if isinstance(from_room, str):
            from_room = _rooms.room(from_room)
        if isinstance(dest_room, str):
            dest_room = _rooms.room(dest_room)
        for item in from_room.items:
            _ = f"{_}\n;## {item.name} moved from {from_room.name} to {dest_room.name}"
            dest_room.add_item(item)
        from_room.items.clear()
        return _

    @classmethod
    def move_items(cls, substring: str, from_room: RoomDescription | str, dest_room: RoomDescription | str) -> str:
        global _rooms
        _: str = ""
        if isinstance(from_room, str):
            from_room = _rooms.room(from_room)
        if isinstance(dest_room, str):
            dest_room = _rooms.room(dest_room)
        for item in from_room.items.copy():
            if substring.lower() in item.name.lower():
                _ = f"{_}\n;## {item.name} moved from {from_room.name} to {dest_room.name}"
                dest_room.add_item(item)
                from_room.items.remove(item)
        return _

    @classmethod
    def move_alive(cls, from_room: RoomDescription | str, dest_room: RoomDescription | str) -> str:
        global _rooms
        _: str = ""
        if isinstance(from_room, str):
            from_room = _rooms.room(from_room)
        if isinstance(dest_room, str):
            dest_room = _rooms.room(dest_room)
        for item in from_room.items.copy():
            if isinstance(item, CharacterSheet):
                if item.is_alive:
                    _ = f"{_}\n;## {item.name} moved from {from_room.name} to {dest_room.name}"
                    dest_room.add_item(item)
                    from_room.items.remove(item)
        return _


_rooms: Rooms = Rooms()


def rooms_status() -> str:
    global _rooms
    lines: list[str] = list()
    for room in _rooms.rooms.values():
        v: str = "" if room.new_visit else " (visited)"
        v: str = " *** COMPLETED" if room.complete else v
        lines.append(f"{room.name}{v}: {room.notes}")
    lines.sort()
    _ = ""
    for line in lines:
        _ += f"\n;## {line}"
    return _


def rooms_notes() -> str:
    _ = ""
    room_ids: list[str] = [key for key in _rooms.rooms.keys()]
    room_ids.sort()
    for room_id in room_ids:
        room = _rooms.room(room_id)
        _ += f"\n;## {room.name}: {room.notes}"
    return _


def rooms_random_loot(seed: int = 0):
    r = random.Random(seed)
    for room in _rooms.rooms.values():
        if r.randint(1, 100) <= 33:
            if room.notes:
                room.notes = f"{room.notes}, {loot(r)}"
            else:
                room.notes = loot(r)


def rooms_random_encounters(seed: int = 0):
    r = random.Random(seed)
    for room in _rooms.rooms.values():
        qty: int = r.randint(1, 4)
        creatures: str = r.choice(
                ["Bears", "Large Cats", "Fire Beetles", "Giant Beetles", "Giant Rats", "Giant Spiders", "Dire Wolves",
                 "Earth Elementals", "War Golems", "Warrior Skeletons", "Archer Skeletons", "Zombies"])
        if r.randint(1, 100) <= 40:
            if room.notes:
                room.notes = f"{room.notes}, {qty} {creatures}"
            else:
                room.notes = f"{qty} {creatures}"


def rooms_reset() -> None:
    for room in _rooms.rooms.values():
        room.views = 0
        room.new_visit = True
        room.complete = False
        room.items.clear()


def rooms_clear_notes() -> None:
    for room in _rooms.rooms.values():
        room.notes = ""
        room.new_visit = True


def rooms(room_id: str) -> RoomDescription:
    global _rooms
    return _rooms.room(room_id)


def save_rooms() -> str:
    global _rooms
    return _rooms.save_rooms()


def restore_rooms(pickled: str) -> None:
    global _rooms
    _rooms.restore_rooms(pickled)


# preload various initial room descriptions
_ = rooms("2")
_._desc1 = "You follow the passage for 50ft and come to a cave with a tiled floor. You see a stone plinth on the far " \
          "side holding a two handed war axe. Even from this distance you can tell that it is a finely crafted " \
          "weapon. Next to the plinth on the floor you see the remains of a monk with several arrows in its back. It " \
          "looks like the monk was trying to reach the axe before being struck down. As you look beyond the dead monk " \
          "you see figures moving into the torchlight."
_._desc2 = "Tiled floor cave with stone plinth"
_.notes = "Dead monk with arrows in back next to plinth. Axe on plinth. 1d3 skeletons. 1d4 zombies."
_.directions["w"] = "3way"
_.directions["search"] = "2-wall"

_ = rooms("2-wall")
_._desc1 = "As you continue searching the walls, a spectral hand suddenly reaches out, grabs you, and pulls you into " \
          "the now insubstantial wall. You are never heard from again. "

_ = rooms("3")
_._desc1 = "You enter a 90ft x 40ft room full of wine and ale casks. Many are open. You don't see any other doors or " \
          "passages leading from the room. "
_._desc2 = "You enter the room full of empty and broken casks."
_.notes = "1d4 giant rats nesting in casks"
_.directions["n"] = "3way"

_ = rooms("4")
_._desc1 = "You step into a natural cave. Water oozes down the walls and" \
          " forms a 30ft diameter pond in the middle of it. You " \
          "notice water dripping from the cave roof about 30ft above." \
          " From the pond a rivulet of water heads into a large " \
          "crack in the middle of the wall /S/ which appears large enough to walk into." \
          " The pond is covered in what appears to be a dark green " \
          "scummy algae. "
_._desc2 = "You are in the cave with a pond in the middle." \
          " There is a large crack in the wall /S/." \
          " The cave entrance is /E/."
_.notes = "1d3 Giant Spiders in crack. Will attack if pond is searched and looted."
_.directions["s"] = "4a"
_.directions["e"] = "4way"
_.directions["pond"] = "4-pond"

_ = rooms("4a")
_._desc1 = "You enter a very large crack in the cave wall and go about 30 ft." \
          " The ground is sloped here. Up slope is /S/."
_._desc2 = "You enter a very large crack in the cave wall. The ground is sloped here." \
          " Down is /N/."
_.notes = "1d3 Giant Spiders"
_.directions["s"] = "4b"
_.directions["n"] = "4"

_ = rooms("4-pond")
_._desc1 = " You step into the pond and grope around feeling along its rough bottom." \
          " When you reach the center you notice the " \
          "texture suddenly becomes very smooth. Feeling around a little more you find an edge you can pull " \
          "up on. You pull up on the edge and a large metal" \
          " plate comes to the surface in your grasp. You toss the plate aside and feel down " \
          "where it was. You find a shallow depression with a sack in it. "
_._desc2 = "You are standing in a pond covered in algae in a cave."
_.notes = ":Set the sack down and fight :Loot sack and equip anything found before fighting"
_.directions["out"] = "4"

_ = rooms("5")
_._desc1 = "You come to a portcullis. Beyond you see a 90ft x 40ft room with" \
          " alcoves in the walls. You can't see into the alcoves from here." \
          " You push the portcullis open with the sound of rusted screeching metal" \
          " and step into the room. You can now see into the alcoves " \
          "and notice they are filled with the skeletons and corpses of monks, except one" \
          " in the wall /E/ in the near corner."
_._desc2 = "You return to the crypt. The portcullis is /S/. The empty alcove is /E/."
_.notes = "1d3 Skeletons, 1d4 Zombies"
_.directions["s"] = "4way"
_.directions["e"] = "5a"

_ = rooms("5a")
_._desc1 = "You walk over to the alcove and discover a cleverly disguised door. Opening " \
          "it and stepping in, you find yourself in a 40ft x 30ft room." \
          " All the walls are covered with depictions of evil and bloody looking acts. On the far " \
          " wall you see a mummified corpse that is tied with barbed wire to a wooden X." \
          " A small open chest /E/ is " \
          " in the far corner of the room. "
_._desc2 = "You are in a 30ft x 40ft room with a dead monk on an X cross. The entrance /W/."
_.notes = ""
_.add_item(Item("Open chest"))
_.directions["w"] = "5"

_ = rooms("3way")
_._desc1 = "You are at a three way intersection with openings /N/, /E/, and /S/." \
          " The passageway /E/ disappears into darkness." \
          " The passageway /N/ disappears into darkness." \
          " The passageway /S/ goes for 10ft past the intersection and ends at " \
          " a set of stairs heading down. "
_._desc2 = "You return to the three way. You see passageways /E/, /N/, and /S/." \
          " The passage /S/ ends after 10ft at a flight of stairs heading down."
_.notes = ""
_.directions["n"] = "4way"
_.directions["e"] = "2"
_.directions["s"] = "3"

_ = rooms("4way")
_._desc1 = "You are at a four way intersection." \
          " You came in from the passage /E/. Passages /N/, /S/, and /W/ disappear into darkness. "
_._desc2 = "You are at a four way intersection. The passage /E/ leads to the ruins above."
_.notes = ""
_.directions["n"] = "5"
_.directions["e"] = "1"
_.directions["s"] = "3way"
_.directions["w"] = "4"

_ = rooms("1")
_._desc1 = "You see a flight of stairs and come to a short 10ft passageway" \
          " which ends at a wall with an opening to another " \
          "flight of stairs heading down into darkness. "
_._desc2 = "You travel down a 100ft passage and come to a bend. A flight of stairs leads up /N/."
_.directions["w"] = "4way"
_.directions["n"] = "1b"
_.directions["up"] = "1b"

_ = rooms("1b")
_._desc1 = "You are in the ruins of the abbey next to a flight of stairs heading down into the earth."
_.directions["down"] = "1"
_.directions["town"] = "town"

_ = rooms("4b")
_._desc1 = "You continue up slope and come to an opening. Stepping through you find that" \
          " you are on the hillside with the ruins of the abbey a short ways above. You" \
          " have discovered another way in and out of the complex."
_._desc2 = "You continue up slope and step through the entrance. You are on the hillside with the ruins above."
_.directions["n"] = "4a"
_.directions["down"] = "town"
_.directions["town"] = "town"

_ = rooms("start")
_._desc1 = "Welcome New Adventurer"

_ = rooms("town")
_._desc1 = "You make your way downhill and then trek back to town." \
          " You take the time to rest and heal overnight at the inn. Early the next morning " \
          "you head to the various shops in town to discover what loot you have gained."
