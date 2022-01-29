from dataclasses import dataclass


@dataclass(slots=True)
class CharacterTalent:
    name: str = ""
