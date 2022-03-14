#!/usr/bin/env bash
"""true" '''\'
set -e
eval "$(conda shell.bash hook)"
conda deactivate
conda activate WyRM
exec python "$0" "$@"
exit $?
''"""
from gb_compiler import GamebookCompiler
from lark import UnexpectedCharacters
from lark import Lark


def basic_escape(text: str) -> str:
    return text.replace("\\", "\\\\\"").replace("\"", "\\\"")


def main() -> None:
    global indent_depth
    q3 = "\"\"\""
    q1 = "\""
    parser: Lark
    with open("lark/gamebook.lark") as r:
        # parser = Lark(r, cache=None, parser="earley", lexer="dynamic_complete", ambiguity="resolve")  # parser="lalr")
        parser = Lark(r, cache=None, parser="lalr", propagate_positions=True)
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

    gbc: GamebookCompiler = GamebookCompiler()  # gbi.visit(tree)
    with open("gamebooks/gb1.py", "w") as w:
        program: str = gbc.visit(tree)
        for part in program:
            w.write(part)
        w.write("\n")


if __name__ == '__main__':
    main()
