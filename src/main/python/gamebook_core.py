import abc
import dataclasses
from abc import ABC


@dataclasses.dataclass(slots=True)
class AbstractItem(ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        return ""


@dataclasses.dataclass(slots=True)
class AbstractCharacter(ABC):
    pass


@dataclasses.dataclass
class Facing:
    _facing: int = 0
    _facing_subj: dict[int, str] = dataclasses.field(default_factory=dict)
    _facing_obj: dict[int, str] = dataclasses.field(default_factory=dict)
    _direction_as_option: dict[int, str] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        self._facing: int = 0

        self._facing_subj[0] = "front"
        self._facing_subj[1] = "right"
        self._facing_subj[2] = "rear"
        self._facing_subj[3] = "left"

        self._direction_as_option[0] = "Continue forwards."
        self._direction_as_option[1] = "Turn right and continue."
        self._direction_as_option[2] = "Go back."
        self._direction_as_option[3] = "Turn left and continue."

        self._facing_obj[0] = "north"
        self._facing_obj[1] = "east"
        self._facing_obj[2] = "south"
        self._facing_obj[3] = "west"

    def face(self, direction: str):
        self.facing = direction

    def with_facing(self, direction: str) -> "Facing":
        self.facing = direction
        return self

    def is_facing(self, direction: str) -> bool:
        if not direction:
            return False
        direction = direction.lower()[0]
        return direction == self.facing

    def is_behind(self, direction: str) -> bool:
        if not direction:
            return False
        direction = direction.lower()[0]
        if direction == "n":
            return self.n == "rear"
        elif direction == "e":
            return self.e == "rear"
        elif direction == "s":
            return self.s == "rear"
        return self.w == "rear"

    @property
    def behind(self) -> str:
        txt: str = ""
        if self.facing == "n":
            return "s"
        elif self.facing == "e":
            return "e"
        elif self.facing == "s":
            return "n"
        return "e"

    @property
    def compass(self) -> str:
        return self._facing_obj[self._facing]

    @property
    def facing(self) -> str:
        if self._facing == 0:
            return "n"
        if self._facing == 1:
            return "e"
        if self._facing == 2:
            return "s"
        if self._facing == 3:
            return "w"
        return "UNKNOWN"

    def subj_idx(self, direction: int) -> int:
        return (4 - self._facing + direction) % 4

    @facing.setter
    def facing(self, facing: str) -> None:
        if not facing:
            return
        facing = facing.strip().lower()[0]
        if facing == "n":
            self._facing = 0
            return
        if facing == "e":
            self._facing = 1
            return
        if facing == "s":
            self._facing = 2
            return
        if facing == "w":
            self._facing = 3
            return
        print(f"Unknown facing: {facing}")

    @property
    def n(self) -> str:
        return self._facing_subj[self.subj_idx(0)]

    @property
    def e(self) -> str:
        return self._facing_subj[self.subj_idx(1)]

    @property
    def s(self) -> str:
        return self._facing_subj[self.subj_idx(2)]

    @property
    def w(self) -> str:
        return self._facing_subj[self.subj_idx(3)]

    # _direction_as_option

    @property
    def dn(self) -> str:
        return self._direction_as_option[self.subj_idx(0)]

    @property
    def de(self) -> str:
        return self._direction_as_option[self.subj_idx(1)]

    @property
    def ds(self) -> str:
        return self._direction_as_option[self.subj_idx(2)]

    @property
    def dw(self) -> str:
        return self._direction_as_option[self.subj_idx(3)]


class Items:
    _inv: list[AbstractItem] = list()

    def __init__(self):
        self._inv: list[AbstractItem] = list()

    def add(self, item: AbstractItem):
        self._inv.append(item)

    def drop(self, item: AbstractItem):
        if isinstance(item, AbstractItem):
            self._inv.remove(item)
            return

    def item(self, item_name: str) -> AbstractItem:
        for item in self._inv:
            if item.name.startswith(item_name):
                return item

    def clear(self) -> None:
        self._inv.clear()

    @property
    def inv(self) -> str:
        result: str = ""
        if not self._inv:
            return ""

        names: list[str] = list()
        for item in self._inv:
            names.append(item.name)
        names.sort()

        result = ""
        for name in names:
            if name:
                if result:
                    result += ", "
                result += name

        x = len(self._inv)
        if x == 1:
            result = "\n\nItem: " + result
        else:
            result = "\n\nItems:" + result

        return result + "\n\n"


_turn: list[int] = [0]


def next_turn() -> None:
    global _turn
    _turn.append(_turn[-1]+1)


def turn() -> int:
    global _turn
    return _turn[-1]


def restore_turn() -> None:
    global _turn
    if len(_turn) > 1:
        _turn.pop(-1)
