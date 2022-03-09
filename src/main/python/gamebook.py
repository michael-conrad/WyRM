#!/usr/bin/env bash
"""true" '''\'
set -e
eval "$(conda shell.bash hook)"
conda deactivate
conda activate WyRM
exec python "$0" "$@"
exit $?
''"""

from gb_interpreter import GamebookInterpreter
from lark import UnexpectedCharacters
from lark import Lark


def main() -> None:
    parser: Lark
    with open("lark/gamebook.lark") as r:
        parser = Lark(r, ambiguity="resolve")
    gb: str
    with open("gamebooks/gb1.gb") as r:
        gb = r.read()
    try:
        tree = parser.parse(gb)
    except UnexpectedCharacters as e:
        print(e)
        for rule in e.considered_rules:
            print(f" - {rule}")
            break
        return

    with open("gamebooks/gb1.tree.txt", "w") as w:
        w.write(tree.pretty())
        w.write("\n")
    gbi: GamebookInterpreter = GamebookInterpreter()
    gbi.visit(tree)


if __name__ == '__main__':
    main()
