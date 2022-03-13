import html

import lark.visitors

from lark import Token
from lark import Tree


def unescape(text: str) -> str:
    return text.encode('utf-8').decode('unicode-escape')


def escape(text: str) -> str:
    return text.encode('unicode-escape').decode('utf-8')


def basic_escape(text: str) -> str:
    return text.replace("\\", "\\\\\"").replace("\"", "\\\"")


def basic_unescape(text: str) -> str:
    return text.replace("\\\"", "\"").replace("\\\\\"", "\\",)


indent: int = 0
out = print


def print(*args, **kwargs):
    out("    "*indent, end='')
    out(*args, **kwargs)


class GamebookCompiler(lark.visitors.Interpreter):
    q1 = "\""
    q3 = "\"\"\""

    once_counter: int = 0
    section_ctr: int = 0
    section_pad_length: int = 1
    state_track_set: set[str] = set()

    section_lookup: dict[str, str] = dict()
    var_lookup: dict[str, str] = dict()

    _next_random_seed: int = 0

    @property
    def next_random_seed(self) -> int:
        self._next_random_seed += 1
        return self._next_random_seed

    def start(self, tree: Tree | Token):
        global indent
        self.visit_children(tree)

    def metadata(self, tree: Tree | Token):
        import_block: list[str] = list()
        info_block: list[tuple[str, str]] = list()
        info_tags: set[str] = set()
        for child in tree.children:
            if isinstance(tree, Token):
                print(f"token: {tree.type} = {tree.value}")
                continue
            if child.data == "metadata_entry":
                tag, value = child.children
                if tag == "Library":
                    import_block.append(f"{value.strip()}")
                else:
                    if tag in info_tags:
                        raise SyntaxError(f"Duplicate entry {tag}. Each metadata entry must be uniquely tagged.")
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

        # special imports and other early data to set
        print(f"import random")
        print(f"from jsonpickle import decode, encode")
        print(f"from types import SimpleNamespace")
        print()
        print()

        if info_block:
            print("# Game Book Metadata")
            print()
            print("gamebook_metadata: dict[str, str] = dict()")
        for tag, value in info_block:
            print(f"gamebook_metadata[\"{tag}\"] = \"{value}\"")
        if info_block:
            print()

    def sections(self, tree: Tree):
        global indent
        self.section_pad_length = len(str(len(tree.children)))

        # add the predefined dict, world, pointing to package locals
        print("# Hard coded predefines")
        print(f"# pad: {self.section_pad_length}")
        print()
        print("state: SimpleNamespace = SimpleNamespace()")
        print("state.world = SimpleNamespace()")
        print("state.world.turn = 0")
        print("state.world.facing = \"\"")
        print("state.world.location = \"\"")
        print("recurse_depth: int = 0")
        print()
        print("# Intentionally not tracked in state")
        print("_node_id: int = 0")
        print()
        print()
        print("def new_label() -> str:")
        indent += 1
        print("global _node_id")
        print("_node_id += 1")
        print('return f"{_node_id:08x}"')
        indent -= 1
        print()
        print()
        print("_output: dict[str, str] = dict()")
        print()
        self.state_track_set.add('state')
        self.state_track_set.add('recurse_depth')

        # scan ahead for section names to build section to function lookup table
        for child in tree.children:
            if isinstance(child, Tree):
                for child2 in child.children:
                    if isinstance(child2, Token):
                        if child2.type == "SECTION_NAME":
                            self.section_ctr += 1
                            name: str = child2.value
                            section_name = f"section_{self.section_ctr:0{self.section_pad_length}}"
                            self.section_lookup[name] = section_name
        self.visit_children(tree)

        print()
        print()
        print("def save_state() -> dict[str, str]:")
        indent += 1
        for state in self.state_track_set:
            print(f"global {state}")
        print("states: dict[str, str] = dict()")
        for state in self.state_track_set:
            print(f"states['{state}'] = jsonpickle.encode({state})")
        print("return states")
        indent -= 1
        print()
        print()
        print("def restore_state(states: dict[str, str]) -> None:")
        indent += 1
        for state in self.state_track_set:
            print(f"global {state}")
        for state in self.state_track_set:
            print(f"{state} = jsonpickle.decode(states['{state}'])")
        print()
        print("return")

    def section(self, tree: Tree):
        global indent
        for child in tree.children:
            if isinstance(child, Tree):
                self.visit(child)
                continue
            if isinstance(child, Token):
                if child.type == "NL":
                    continue
                if child.type == "SECTION_NAME":
                    self.section_ctr += 1
                    name = child.strip()
                    section_name = self.section_lookup[name]
                    # section_name = f"section_{self.section_ctr:0{self.section_pad_length}}"
                    self.section_lookup[name] = section_name
                    print(f"state.{section_name} = SimpleNamespace()")
                    print(f"state.{section_name}.metadata = dict[str, str] = dict()")
                    print(f"state.{section_name}.once = set[int] = set()")
                    print(f"state.{section_name}.vars = dict[str, any] = dict()")
                    print()
                    print()
                    print(f"def {section_name}() -> str:")
                    indent += 1
                    value: str = basic_escape(f"{name}")
                    print(f"{self.q3}{value}{self.q3}")
                    print()
                    print("global _output")
                    print("global state")
                    print("global recurse_depth")
                    print("recurse_depth += 1")
                    print("if recurse_depth > 10_000:")
                    print("    raise RecursionError()")
                    print(f"section: str = {self.q1}{value}{self.q1}")
                    print()
                    print(f"_state: SimpleNamespace = state.{section_name}")
                    print(f"_metadata: dict[str, str] = _state.metadata")
                    print(f"_once: set[int] = _state.once")
                    print(f"_vars: dict[str, any] = _state.vars")
                    self.once_counter += 1
                    print()
                    print(f"if {self.once_counter} not in _once:")
                    indent += 1
                    print(f"_once.add({self.once_counter})")
                    print(f"state.{section_name}.random_state = random.Random({self.next_random_seed}).getstate()")
                    indent -= 1
                    print()
                    print("out: str = ''")
                    print(f"rand = random.Random()")
                    print(f"rand.setstate(state.{section_name}.random_state)")
                    print()
                    continue
                print(f"Unknown token: {child.type} = {child.value}")
                continue
        print(f"node_id: str = new_label()")
        print("_output[node_id] = out")
        print("return node_id")
        indent -= 1
        print()

    def section_metadata(self, tree: Tree):
        global indent
        self.once_counter += 1
        print(f"if {self.once_counter} not in _once:")
        indent += 1
        print(f"_once.add({self.once_counter})")
        self.visit_children(tree)
        indent -= 1
        print()

    def section_metadata_entry(self, tree: Tree | Token):
        tag, value = tree.children[:2]
        print(f"metadata[{self.q1}{tag}{self.q1}] = {value}")

    def section_content(self, tree: Tree):
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == "direction_stmt":
                    continue
                if child.data == "option_stmt":
                    continue
                self.visit(child)
                continue
            if isinstance(child, Token):
                print(child.value)
                continue
        print("# OPTIONS")
        print()
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == "option_stmt":
                    print(f"saved_state = save_state()")
                    self.visit(child)
                    print(f"restore_state(saved_state)")
                    print(f"rand.setstate(_state.random_state)")
                    print()

        print("# DIRECTIONS")
        print()
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == "direction_stmt":
                    print(f"saved_state = save_state()")
                    self.visit(child)
                    print(f"restore_state(saved_state)")
                    print(f"rand.setstate(_state.random_state)")
                    print()

    def direction_stmt(self, tree: Tree):
        if len(tree.children) == 3:
            section_name: str = basic_unescape(tree.children[1].value[1:-1])
            if section_name not in self.section_lookup:
                raise KeyError(f"Section {section_name} not found. Valid sections: {[k for k in self.section_lookup.keys()]}")
            section_func: str = self.section_lookup[section_name]
            print(f"dest: str = {section_func}()  # {section_name}")
            d: str = ""
            d += "out += f\""
            d += f"<a href=\\{self.q1}"
            d += "{dest}"
            d += f".html\\{self.q1}>"
            d += html.escape(section_name).strip()
            d += '</a>"'
            print(d)
        elif len(tree.children) == 4:
            pass  #_, desc,
        else:
            print(f"# {len(tree.children)} {tree.data} {tree.children}")

    def short_comment(self, tree: Tree):
        comment: str = tree.children[0]
        print(f"# {comment[1:].strip()}")

    def long_comment(self, tree: Tree):
        print()
        comment: str = tree.children[0]
        for line in comment[3:-3].strip().split("\n"):
            print(f"# {line}")
        print()

    def say_stmt(self, tree: Tree):
        for child in tree.children:
            if isinstance(child, Token):
                markdown = tree.children[0]
                print(f"md = {markdown}")
                print(f'out += "\\n\\n"')
                print(f"out += md.rstrip()")
                print()
            else:
                markdown = self.visit(child)
                print(markdown)

    def __default__(self, tree: Tree | Token):
        print(f"other: {tree.data}")
        self.visit_children(tree)
