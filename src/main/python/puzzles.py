import dataclasses


@dataclasses.dataclass
class WallButtonsPuzzle:
    states: dict[str, bool | None] = dataclasses.field(default_factory=dict)

    @property
    def solved(self) -> bool:
        return False

    def __post_init__(self):
        self.states["2"] = None
        self.states["4"] = None
        self.states["5"] = None
        self.states["5a"] = None

    def push_button(self, location: str, button: str) -> str:
        if location not in self.states:
            self.states[location] = None
        prev: str = "All buttons were up." \
            if self.states[location] is None \
            else self.states[location]

        self.states[location] = button




