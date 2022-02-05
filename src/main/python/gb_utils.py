import dice


def roll(die: str) -> int:
    if die.strip()[-1]!="t":
        die += " t"
    return dice.roll(f"{str}")
