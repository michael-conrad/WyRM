#!/usr/bin/env bash
"""true" '''\'
set -e
eval "$(conda shell.bash hook)"
conda deactivate
conda activate WyRM
exec python "$0" "$@"
exit $?
''"""
import lark.visitors

from lark import Lark
from lark import Tree


class GamebookInterpreter(lark.visitors.Interpreter):
    gb_metadata: dict[str, list[str]] = dict()
    globals: dict = dict()
    locals: dict = dict()

    def metadata_tag(self, tree: Tree):
        tag: str = tree.children[0].strip()
        value: str = tree.children[1].strip()
        if tag not in self.gb_metadata:
            self.gb_metadata[tag] = list()
        self.gb_metadata[tag].append(value)

        if tag.lower() == "library":
            exec(f"import {value}", self.globals)


def main() -> None:
    parser: Lark
    with open("gamebook.lark") as r:
        parser = Lark(r)
    gb: str
    with open("gamebooks/gb1.gb") as r:
        gb = r.read()
    with open("gamebooks/gb1.tree.txt", "w") as w:
        tree = parser.parse(gb)
        w.write(tree.pretty())
        w.write("\n")
    gbi:GamebookInterpreter = GamebookInterpreter()
    gbi.visit(tree)
    print(gbi.globals.keys())




if __name__ == '__main__':
    main()
