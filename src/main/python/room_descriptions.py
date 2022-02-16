import textwrap
from copy import deepcopy
from dataclasses import dataclass
from dataclasses import field

import jsonpickle


@dataclass(slots=True)
class RoomDescription:
    name: str = ""
    desc1: str = ""
    desc2: str = ""
    notes: str = ""
    items: list[str] = field(default_factory=list)
    new_visit: bool = True
    views: int = 0

    def __str__(self):
        self.views += 1
        desc = self.desc1 if self.new_visit else self.desc2
        if not desc:
            desc = self.desc1
        self.new_visit = False
        _: str = ""
        for line in textwrap.wrap(desc, tabsize=4):
            _ += f";##  {line}\n"
        desc = _

        result: str = f""
        result += f"ROOM: {self.name} ({self.views:,})\n"
        result += f"{desc}"
        if self.items:
            result += ";##  Items: " + str(self.items) + "\n"
        if self.notes:
            result += ";##  Notes: " + str(self.notes) + "\n"
        return result


@dataclass(slots=True)
class Rooms:
    rooms: dict[str, RoomDescription] = field(default_factory=dict)

    def room(self, name: str) -> RoomDescription:
        if name not in self.rooms:
            this_room: RoomDescription = RoomDescription(name=f"{name}")
            this_room.desc1 = f"ROOM {name} NOT FOUND!"
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


_rooms: Rooms = Rooms()


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
_.desc1 = "You follow the passage for 50ft and come to a cave with a tiled floor. You see a stone plynth on the far " \
          "side holding a two handed war axe. Even from this distance you can tell that it is a finely crafted " \
          "weapon. Next to the plynth on the floor you see the remains of a monk with several arrows in its back. It " \
          "looks like the monk was trying to reach the axe before being struck down. As you look beyond the dead monk " \
          "you see figures moving into the torchlight."
_.desc2 = "Tiled floor cave with stone plynth"
_.notes = "Dead monk with arrows in back next to plynth. Axe on plynth. 1d3 skeletons. 1d4 zombies."

_ = rooms("3")
_.desc1 = "90ft x 40ft room full of wine and ale casks many of which appear busted open. You don't see any doors or " \
          "passages in the room. "
_.desc2 = "room of broken casks"
_.notes = "1d4 giant rats nesting in casks"

_ = rooms("4")
_.desc1 = "a natural cave. Water oozes down the walls and forms a 30ft diameter pond in the middle of it. You " \
          "notice water dripping from the cave roof about 30ft above." \
          " From the pond a rivulet of water heads into a large " \
          "crack in the middle of the left wall which appears large enough to walk into." \
          " The pond is covered in what appears to be a dark green " \
          "scummy algae. "
_.desc2 = "Cave with pond in the middle. Crack in (S) wall."
_.notes = "1d3 Giant Spiders in crack. Will attack if pond is searched and looted."

_ = rooms("4a")
_.desc1 = "You enter a very large crack in the cave wall and go about 30 ft and notice the" \
          " ground starting to slope upwards."
_.desc2 = "Inside crack in cave wall"
_.notes = "1d3 Giant Spiders"

_ = rooms("4-pond")
_.desc1 = " You step into the pond and grope around feeling along its rough bottom." \
          " When you reach the center you notice the " \
          "texture suddenly becomes very smooth. Feeling around a little more you find an edge you can pull " \
          "up on. You pull up on the edge and a large metal" \
          " plate comes to the surface in your grasp. You toss the plate aside and feel down " \
          "where it was. You find a shallow depression with a sack in it. "
_.desc2 = "You are standing in a pond covered in algae in a cave."
_.notes = ":Set the sack down and fight :Loot sack and equip anything found before fighting"

_ = rooms("5")
_.desc1 = "You come to a portcullis. Beyond you see a 90ft x 40ft room with" \
          " alcoves in the walls. You can't see into the alcoves from here." \
          " You push the portcullis open with the sound of rusted screeching metal" \
          " and step into the room. You can now see into the alcoves " \
          "and notice they are filled with the skeletons and corpses of monks, except one." \
          " Which is in the right wall in the near corner."
_.desc2 = "Crypt of dead monks"
_.notes = "1d3 Skeletons, 1d4 Zombies"

_ = rooms("5a")
_.desc1 = "a 40ft x 30ft room. All the walls are covered with depictions of evil and bloody looking acts. On the far E " \
          "wall you see a mummified corpse that is tied with barbed wire to a wooden X. There is a small open chest " \
          "in the far corner of the room to the NE. "
_.desc2 = "A room with a dead monk on an X cross."
_.notes = ""

_ = rooms("3way")
_.desc1 = "You are at a three way intersection with openings to the N, E, and S." \
          " The passageway E disappears into darkness." \
          " The passageway N disappears into darkness." \
          " The passageway S goes for 10ft past the intersection and ends at " \
          "a set of stairs heading down. "
_.desc2 = "You are at a three way. E, N, S. S is stairs heading down."
_.notes = ""

_ = rooms("4way")
_.desc1 = "A four way intersection." \
          " E is where you came in. N, S, W disappear into darkness. "
_.desc2 = "Four way intersection. E is dungeon entrance."
_.notes = ""

_ = rooms("1")
_.desc1 = "a flight of stairs and come to a short 10ft passageway which ends at a wall with an opening to another " \
          "flight of stairs heading down into darkness. "
_.desc2 = "Flight of stairs at surface"

_ = rooms("start")
_.desc1 = "Welcome New Adventurer"
