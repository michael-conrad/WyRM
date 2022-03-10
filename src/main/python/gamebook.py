#!/usr/bin/env bash
"""true" '''\'
set -e
eval "$(conda shell.bash hook)"
conda deactivate
conda activate WyRM
exec python "$0" "$@"
exit $?
''"""
from contextlib import redirect_stdout

from lark import Token

from lark import Tree
from lark import UnexpectedCharacters
from lark import Lark


indent_depth: int = 0
out = print


def print(*args, **kwargs):
    global indent_depth
    if args:
        out("    " * indent_depth, end='')
    out(*args, **kwargs)


def basic_escape(text: str) -> str:
    return text.replace("\\", "\\\\\"").replace("\"", "\\\"")


def main() -> None:
    global indent_depth
    q3 = "\"\"\""
    q1 = "\""
    parser: Lark
    with open("lark/gamebook.lark") as r:
        parser = Lark(r, parser="earley", ambiguity="resolve")  # parser="lalr")
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

    with open("gamebooks/gb1.py", "w") as w:
        with redirect_stdout(w):
            for cmd in tree.children:
                if cmd.data == "metadata":
                    import_block: list[str] = list()
                    info_block: list[tuple[str, str]] = list()
                    info_tags: set[str] = set()
                    for child in cmd.children:
                        if child.data == "metadata_entry":
                            tag, value = child.children
                            if tag == "Library":
                                import_block.append(f"{value.strip()}")
                            else:
                                if tag in info_tags:
                                    raise SyntaxError(
                                        f"Duplicate entry {tag}. Each metadata entry must be uniquely tagged.")
                                info_tags.add(tag)
                                value: str = basic_escape(f"{value.strip()}")
                                info_block.append((tag.strip(), value))
                    if import_block:
                        print("# Imports from library metadata")
                        print()
                    for import_lib in import_block:
                        print(f"import {import_lib}")
                    if import_block:
                        print()

                    if info_block:
                        print("# Game Book Metadata")
                        print()
                        print("gamebook_metadata: dict[str, str] = dict()")
                    for tag, value in info_block:
                        print(f"gamebook_metadata[\"{tag}\"] = \"{value}\"")
                    if info_block:
                        print()

                    # add the predefined dict, world, pointing to package locals
                    print("# Hard coded predefines")
                    print("world: dict = globals()")
                    print()
                    print("world[\"turn\"] = 0")
                    print("world[\"facing\"] = \"\"")
                    print("world[\"location\"] = \"\"")
                    print()
                elif cmd.data == "sections":
                    sections: list = cmd.children
                    print("# SECTIONS")
                    once_counter: int = 0
                    section_counter: int = 0
                    lead_count: int = len(str(len(sections)))
                    for section in sections:
                        section_name: str
                        if isinstance(section, Tree) and section.data == "section":
                            for sec_part in section.children:
                                if isinstance(sec_part, Token):
                                    if sec_part.type == "NL":
                                        continue
                                    if sec_part.type == "SECTION_NAME":
                                        name = sec_part.value
                                        section_counter += 1
                                        section_name = f"section_{section_counter:0{lead_count}}"
                                        print(f"{section_name}_metadata: dict[str, str] = dict()")
                                        print(f"{section_name}_once: set[int] = set()")
                                        print()
                                        print()
                                        print(f"def {section_name}():")
                                        indent_depth += 1
                                        value: str = basic_escape(f"{name.strip()}")
                                        print(f"{q3}{value}{q3}")
                                        print()
                                        print("global world")
                                        print(f"global {section_name}_metadata")
                                        print(f"global {section_name}_once")
                                        print()
                                        print(f"metadata: dict[str, str] = {section_name}_metadata")
                                        print(f"once: set[int] = {section_name}_once")
                                        print()
                                        print(f"section: str = {q1}{basic_escape(name)}{q1}")
                                        print()
                                        continue
                                    print(f"# UNKNOWN TOKEN: {sec_part.type} -> {sec_part.value}")
                                    continue
                                if isinstance(sec_part, Tree):
                                    data: str = sec_part.data
                                    if data == "section_metadata":
                                        once_counter += 1
                                        print(f"if {once_counter} not in once:")
                                        indent_depth += 1
                                        print(f"once.add({once_counter})")
                                        for metadata_entry in sec_part.children:
                                            tag, text = metadata_entry.children[:2]
                                            print(f"metadata[{q1}{tag}{q1}] = {text}")
                                        indent_depth -= 1
                                        print()
                                        continue
                                    elif data == "section_content":
                                        for item in sec_part.children:
                                            if isinstance(item, Tree):
                                                if item.data == "long_comment":
                                                    comment: str = item.children[0][3:-3].strip()
                                                    print()
                                                    for _ in comment.split("\n"):
                                                        print(f"# {_}")
                                                    print()
                                                    continue
                                                if item.data == "simple_stmt":
                                                    for simple_stmt in item.children:
                                                        if isinstance(simple_stmt, Tree):
                                                            if simple_stmt.data == "short_comment":
                                                                print(f"# {simple_stmt.children[0][1:].strip()}")
                                                                continue
                                                            if simple_stmt.data == "say_stmt":
                                                                for stmt in simple_stmt.children:
                                                                    if isinstance(stmt, Tree):
                                                                        print (f"say_stmt: {stmt.data}")
                                                                    if isinstance(stmt, Token):
                                                                        print(f"markdown_text = {stmt.value}")
                                                                        print(f"print(markdown_text)")
                                                                        print(f"print()")
                                                                        print()
                                                                continue
                                                            print(f"simple_stmt: {simple_stmt.data}")
                                                        if isinstance(simple_stmt, Token):
                                                            if simple_stmt.type == "NL":
                                                                continue
                                                            print(f"simple_stmt: {simple_stmt.type} = {simple_stmt.value}")

                                                    continue
                                                if item.data == "once_stmt":
                                                    once_counter += 1
                                                    print(f"if {once_counter} not in once:")
                                                    print(f"once.add({once_counter})")
                                                    for stmt in item.children:
                                                        if isinstance(stmt, Tree):
                                                            if stmt.data == "suite":
                                                                indent_depth += 1
                                                                for s in stmt.children:
                                                                    print(s)
                                                                indent_depth -= 1
                                                            print(stmt.data)
                                                        if isinstance(stmt, Token):
                                                            print(stmt.type, stmt.value)
                                                    print()
                                                    continue
                                                print(f"# item: {item.data}")
                                            if isinstance(item, Token):
                                                if item.type == "NL":
                                                    continue
                                                print(f"item: {item.type} = {item.value}")
                                        continue
                                    else:
                                        print("UNKNOWN TREE: {data}")
                                        print(f"data: {sec_part.children}")
                                        continue

                            print(f"return")
                            indent_depth -= 1
                            print()
                            print()

    # gbi: GamebookInterpreter = GamebookInterpreter()  # gbi.visit(tree)


if __name__ == '__main__':
    main()
