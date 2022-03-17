import re
import string
import textwrap

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
    return text.replace("\\\"", "\"").replace("\\\\\"", "\\", )


_indent: int = 0


def indent_inc() -> int:
    global _indent
    _indent += 1
    return _indent


def indent_dec() -> int:
    global _indent
    _indent = max(_indent - 1, 0)
    return _indent


def indent(text: str) -> str:
    global _indent
    _: str = ""
    _ = "    " * _indent + text
    return _


compiled_program: str = ""


def out(text: str = ""):
    global compiled_program
    global _indent
    if "\n" in text:
        for line in text.splitlines(keepends=False):
            out(line)
        return
    text = text.rstrip()
    compiled_program += ("    " * _indent) + text + "\n"


def end_section() -> None:

    out("_output[node_id] += \"\\n\"")
    out("_output[node_id] += \"\\n\"")
    out("for _ in option_list:")
    indent_inc()
    out("saved_state = save_state()")
    out("destination_node = _[1]()")
    out("restore_state(saved_state)")
    out(f"_option_text: str = str(_[0])")
    out(f"_option_text = html.escape(_option_text)")
    out(f"_md_link: str = \"[\" + _option_text + \"](\" + destination_node + \")\"")

    out("_output[node_id] += \"* \" + _md_link")

    out("_output[node_id] += \"\\n\"")

    indent_dec()
    out()
    # out("_output[node_id] = out")
    out("return node_id")
    indent_dec()
    out()
    out()


class GamebookCompiler(lark.visitors.Interpreter):
    q1 = "\""
    q3 = "\"\"\""

    once_counter: int = 0
    section_ctr: int = 0
    section_pad_length: int = 1
    state_track_set: set[str] = set()
    _func_ctr: int = 0

    section_lookup: dict[str, str] = dict()
    section_ctr_lookup: dict[str, int] = dict()
    var_lookup: dict[str, str] = dict()

    _next_random_seed: int = 0

    main_section: str | None = None

    import_block: list[str] = list()

    scope_world: set[str] = set()
    scope_section: set[str] = set()
    scope_local: set[str] = set()

    @property
    def func_ctr(self) -> int:
        return self._func_ctr

    @property
    def next_func(self) -> str:
        self._func_ctr += 1
        return f"inner_{self._func_ctr:06}"

    @property
    def next_direction(self) -> str:
        self._func_ctr += 1
        return f"direction_{self._func_ctr:06}"

    @property
    def next_goto(self) -> str:
        self._func_ctr += 1
        return f"go_{self._func_ctr:06}"

    @property
    def next_option(self) -> str:
        self._func_ctr += 1
        return f"option_{self._func_ctr:06}"

    @property
    def next_random_seed(self) -> int:
        self._next_random_seed += 1
        return self._next_random_seed

    def start(self, tree: Tree) -> str:
        _ = ""
        out("# START")
        out()

        # system required imports
        out("import os")
        out("import html")
        out("import dice")
        out("import hashlib")
        out("import random")
        out("from jsonpickle import decode, encode")
        out("from types import SimpleNamespace")
        out("from collections.abc import Callable")
        out()
        out()

        for child in tree.children:
            if isinstance(child, Token):
                out(child.value)
                continue
            if isinstance(child, Tree):
                _c = self.visit(child)
                if _c:
                    for _d in _c:
                        _ += _d
                continue
        global compiled_program
        _ = compiled_program
        return _

    def metadata(self, tree: Tree | Token):
        out("# Metadata")

        info_block: list[tuple[str, str]] = list()
        info_tags: set[str] = set()
        for child in tree.children:
            if isinstance(tree, Token):
                out(f"token: {tree.type} = {tree.value.strip()}")
                continue
            if child.data == "metadata_entry":
                tag, value, *_ = child.children
                if tag == "Library":
                    self.import_block.append(f"{value.strip()}")
                else:
                    if tag in info_tags:
                        raise SyntaxError(f"Duplicate entry {tag}. Each metadata entry must be uniquely tagged.")
                    info_tags.add(tag)
                    value: str = basic_escape(f"{value.strip()}")
                    info_block.append((tag.strip(), value))
        if self.import_block:
            out("# Imports from library metadata\n")
            out()
        for import_lib in self.import_block:
            out(f"from {import_lib} import *\n")
        if self.import_block:
            out()

        out()
        out()

        if info_block:
            out("# Game Book Metadata\n")
            out()
            out("gamebook_metadata: dict[str, str] = dict()\n")
        for tag, value in info_block:
            out(f"gamebook_metadata[\"{tag}\"] = \"{value}\"\n")
        if info_block:
            out()

    def sections(self, tree: Tree):
        self.section_pad_length = len(str(len([s for s in tree.find_data("section")])))

        # add the predefined dict, world, pointing to package locals
        out("# Sections")
        out(f"# pad: {self.section_pad_length}")
        out("")
        out("repeat_state_tracking: dict[str, str] = dict()")
        out("state: dict[str, any] = dict()")
        out("state['world'] = dict()")
        out("state['world'] = dict()")
        out("state['world']['facing'] = Facing().with_facing('n')")
        out()
        out("def face(facing: str):")
        indent_inc()
        out("global state")
        out("state['world']['facing'].face(facing)")
        indent_dec()
        out()
        out("recurse_depth: int = 0")
        out()
        out(f"imports = dict()")
        for _ in self.import_block:
            out(f"exec('from {_} import *', imports)")
        out(f"for attr in [*imports]:")
        indent_inc()
        out(f"state['world'][attr] = imports[attr]")
        indent_dec()
        out(f"state['world']['__builtins__'] = globals()['__builtins__']")
        out()
        out("# build up list of keys not to pickle or checksum")
        out("ignore_pickle_keys: set[str] = set()")
        out(f"for attr in [*imports]:")
        indent_inc()
        out(f"ignore_pickle_keys.add(attr)")
        indent_dec()
        out(f"ignore_pickle_keys.add('__builtins__')")
        out()
        out("# Intentionally not tracked in state")
        out("_node_id: dict[str, int] = dict()")
        out()
        out()
        out("def new_label(section: str = 'no-section') -> str:")
        indent_inc()
        out("global _node_id")
        out("if section not in _node_id:")
        indent_inc()
        out("_node_id[section]=0")
        indent_dec()
        out("_node_id[section] += 1")
        out("cnt: int = _node_id[section]")
        out('return f"{section}-{cnt:03x}"')
        indent_dec()
        out()
        out()
        out("_output: dict[str, str] = dict()")
        out("node_id_by_checksum: dict[str, str] = dict()")

        # scan ahead for section names to build section to function lookup table

        for child in tree.find_data("section"):
            if isinstance(child, Token):
                continue
            if isinstance(child, Tree):
                if child.data == "section":
                    section_name_block = child
                    self.section_ctr += 1
                    section = section_name_block.children[0]
                    if isinstance(section, Token):
                        name: str = section.value
                        if name in self.section_lookup:
                            raise SyntaxError(f"Section {name} is duplicated")
                        out(f"# {self.section_ctr} {name}")
                        section_name = f"section_{self.section_ctr:0{self.section_pad_length}}"
                        self.section_lookup[name] = section_name
                        self.section_ctr_lookup[name] = self.section_ctr
                        if not self.main_section:
                            self.main_section = name

        _ = ""
        for child in tree.children:
            if isinstance(child, Token):
                out(child.value)
            if isinstance(child, Tree):
                _c = self.visit(child)
                if _c:
                    for _d in _c:
                        _ += _d
        if _:
            out(_)

        # make sure last section function has closing code
        end_section()
        out("section_function_lookup: dict[str, Callable] = dict()")
        for _key in self.section_lookup.keys():
            _function = self.section_lookup[_key]
            out(f"section_function_lookup[\"{_key}\"] = {_function}")

        out()
        out()
        out("def state_checksum() -> str:")
        indent_inc()
        out("pickled: str = jsonpickle.encode(save_state(), keys=True)")
        out("sha512: str = hashlib.sha512(pickled.encode('utf-8')).hexdigest()")
        out("return sha512")
        indent_dec()
        out()
        out()
        out("def save_state() -> dict[str, str]:")
        indent_inc()
        sorted_track = sorted(self.state_track_set)
        out("states: dict[str, str] = dict()")
        out(f"states['world_vars'] = jsonpickle.encode(state['world'], keys=True)")
        for state in sorted_track:
            out(f"states['{state}'] = jsonpickle.encode(state['{state}'], keys=True)")
        out("return states")
        indent_dec()
        out()
        out()
        out("def restore_state(states: dict[str, str]) -> None:")
        indent_inc()
        for state in sorted_track:
            out(f"state['{state}'] = jsonpickle.decode(states['{state}'], keys=True)")
        out(f"state['world'] = jsonpickle.decode(states['world_vars'], keys=True)")
        out("return")
        indent_dec()

        # the first section is 'main'
        out()
        out()
        out(f"index_node: str = {self.section_lookup[self.main_section]}()")
        out("""
os.makedirs("md", exist_ok=True)
for key in _output:
    with open("md/" + key + ".md", "w") as w:
        w.write("\\n")
        w.write("# " + key)
        w.write(_output[key])
        w.write("\\n")
        
with open("md/index.md", "w") as w:
        w.write("\\n")
        w.write("# " + index_node)
        w.write(_output[index_node])
        w.write("\\n")        
""")

    def section(self, tree: Tree):

        # always clear non-world scopes at start of processing a new section
        self.scope_section.clear()
        self.scope_local.clear()

        _ = ""
        for child in tree.children:
            if isinstance(child, Tree):
                self.visit(child)
                continue
            if isinstance(child, Token):
                if child.type == "NL":
                    continue
                if child.type == "SECTION_NAME":
                    name = child.strip()
                    section_name: str = self.section_lookup[name]
                    section_no: int = self.section_ctr_lookup[name]
                    # always make sure previous section has correct return code
                    if section_no > 1:
                        end_section()
                    out(f"# {name}: {section_no}")
                    out()
                    self.section_lookup[name] = section_name
                    self.state_track_set.add(section_name)
                    out(f"state['{section_name}'] = dict()")
                    out(f"state['{section_name}']['name'] = \"{basic_escape(name)}\"")
                    out(f"state['{section_name}']['id'] = {section_no}")
                    out(f"state['{section_name}']['func_name'] = \"{section_name}\"")
                    out(f"state['{section_name}']['metadata'] = dict()")
                    out(f"state['{section_name}']['once'] = set()")
                    out(f"state['{section_name}']['vars'] = dict()")
                    out()
                    out()
                    out(f"def {section_name}() -> str:")
                    indent_inc()
                    value: str = basic_escape(f"{name}")
                    out(f"{self.q3}{value}{self.q3}")
                    out("global _output")
                    out("global state")
                    out("global recurse_depth")
                    out()
                    out(f"_state: dict[str, any] = state['{section_name}']")
                    out(f"_once: set[int] = _state['once']")
                    out(f"_local: dict[str, any] = dict()  # not persistent, discarded after processing")
                    out()
                    out(f"section: str = {self.q1}{value}{self.q1}")
                    out(f"section_name: str = {self.q1}{section_name}{self.q1}")
                    # out("out: str = ''")
                    if self.main_section == name:
                        out("state['world']['facing'] = Facing().with_facing('n')"
                            " # initial assumed facing for first section")

                    out("# see if this is a repeating state, if yes, just use original node id")
                    out("global node_id_by_checksum")
                    out("sha512: str = section"
                        " + ' (' + state['world']['facing'].facing + ') '"
                        " + state_checksum()")
                    out("if sha512 in node_id_by_checksum:")
                    indent_inc()
                    out("return node_id_by_checksum[sha512]")
                    indent_dec()
                    out()
                    out(f"node_id: str = new_label(section_name)")
                    out("_output[node_id] = ''")
                    out("node_id_by_checksum[sha512] = node_id")
                    out()
                    out(f"section_func: Callable = {section_name}")
                    out()
                    out("recurse_depth += 1")
                    out("if recurse_depth > 1000:")
                    indent_inc()
                    out("raise RecursionError()")
                    indent_dec()
                    self.once_counter += 1
                    out()
                    out(f"if {self.once_counter} not in _once:")
                    indent_inc()
                    out(f"_once.add({self.once_counter})")
                    out(f"random.seed({self.next_random_seed})")
                    out(f"state['{section_name}']['random_state'] = random.getstate()")
                    out()

                    indent_dec()
                    out()
                    out(f"random.setstate(state['{section_name}']['random_state'])")
                    out()
                    out("option_list: list[tuple[str, Callable]] = list()")
                    out()

                    continue
                if child.type == "NEWLINE":
                    continue
                out(f"Unknown token: {child.type} = {child.value}")
                continue

            return _

    def statement(self, tree: Tree) -> None:
        _ = ""
        out("# statement")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

    def labeled_statement(self, tree: Tree):
        _ = ""
        out("# labeled statement")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

    def compound_statement(self, tree: Tree):
        _ = ""
        out("# compound statement")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

    def block_item_list(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

    def block_item(self, tree: Tree):
        _ = ""
        out("# block_item")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

    def expression_statement(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(f"segment: str | None = {_.rstrip()}")
            out("if segment is not None:")
            indent_inc()
            # out(f"out += \"\\n\\n\"")
            out(f"_output[node_id] += \"\\n\\n\"")
            out(f"_ = html.escape(str(segment))")
            # out(f"out += textwrap.dedent(_)")
            out(f"_output[node_id] += textwrap.dedent(_)")
            indent_dec()
            out()

    def selection_statement(self, tree: Tree):
        _ = ""
        out("# selection")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

    def __top_level_children(self, children: list[Tree, Token]) -> str:
        _ = ""

        if isinstance(children, Tree):
            children = children.children

        for child in children:
            if isinstance(child, Token):
                if _:
                    _ += ", "
                _ += f"token: {child.type}"
            if isinstance(child, Tree):
                if _:
                    _ += ", "
                _ += f"tree: {child.data}"
        return _

    def if_else_statement(self, tree: Tree):
        out(f"# if else: {len(tree.children)}")
        out(f"# {self.__top_level_children(tree.children)}")
        _, expression, true_block, _, false_block = tree.children

        _ = "if "
        for part in self.visit(expression):
            _ += part
        _ += ':'
        out(_)
        indent_inc()
        self.visit(true_block)
        indent_dec()
        out("else:")
        indent_inc()
        self.visit(false_block)
        indent_dec()

    def if_statement(self, tree: Tree):
        out(f"# if: {len(tree.children)}")
        out(f"# {self.__top_level_children(tree.children)}")
        _, expression, true_block = tree.children

        _ = "if "
        for part in self.visit(expression):
            _ += part
        _ += ':'
        out(_)
        indent_inc()
        self.visit(true_block)
        indent_dec()

    def iteration_statement(self, tree: Tree):
        _ = ""
        out("# iteration")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

    def jump_statement(self, tree: Tree):
        out("# jump")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

    def goto_statement(self, tree: Tree):
        _, new_section, _ = tree.children
        func = self.next_goto
        out(f"def {func}():")
        indent_inc()
        out("global section_function_lookup")
        out("nonlocal _state")
        # out("nonlocal out")
        out()
        # section_function_lookup
        section: str = ""
        for _ in self.visit(new_section):
            section += _
        out(f"lookup: str = str({section})")
        out(f"if lookup not in section_function_lookup:")
        indent_inc()
        out(f"raise KeyError(f\"Section {{lookup}} not found.\")")
        indent_dec()

        out(f"goto_saved_state = save_state()")
        out(f"goto_destination_node: str = section_function_lookup[lookup]()")
        out(f"restore_state(goto_saved_state)")
        out(f"random.setstate(_state['random_state'])")
        out()
        out(f"return goto_destination_node")
        indent_dec()
        out()
        out(f"go_function = {func}")
        out()
        return func

    def comment(self, tree: Tree):
        out("# comment")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

    def direction_statement(self, tree: Tree):
        short_format_string, direction_section, direction_facing, _ = tree.children

        option_bin_description: str = ""
        for child in short_format_string.children:
            if isinstance(child, Token):
                option_bin_description += child.value
        option_bin_description = eval(option_bin_description)

        option_description = ""
        _ = self.visit(short_format_string)
        if _:
            option_description += _

        section_name = ""
        for _ in self.visit_children(direction_section):
            if _:
                section_name += _
        section_name = section_name.strip()[1:-1]

        facing = ""
        for _ in self.visit_children(direction_facing):
            facing += _

        if section_name not in self.section_lookup:
            print(self.__top_level_children(tree.children))
            raise KeyError(f"Section {section_name} not found.\n"
                           f"Valid sections: {[k for k in self.section_lookup.keys()]}")

        section_func: str = self.section_lookup[section_name]

        func: str = self.next_direction
        out(f"# direction statement")
        out()
        out(f"def {func}() -> str:")
        indent_inc()
        out(f"\"\"\"{basic_escape(option_bin_description)}\"\"\"")
        out()
        out()
        out(f"saved_state = save_state()")
        if facing:
            out(f"state['world']['facing'].face({facing})")
        out(f"direction_destination: str = {section_func}() + \".md\"")
        out(f"restore_state(saved_state)")
        out(f"random.setstate(_state['random_state'])")
        out(f"return direction_destination")
        indent_dec()
        out()
        out(f"option_list.append(({option_description}, {func}))")
        out()

    def option_statement(self, tree: Tree):
        _ = ""
        block: Tree = tree.children[1]
        option_description = basic_unescape(tree.children[0][1:-1])
        func: str = self.next_option
        out(f"# option statement")
        out()
        out(f"def {func}() -> str:")
        indent_inc()
        out(f"\"\"\"{basic_escape(option_description)}\"\"\"")
        out()
        out("# new node id is needed")
        out(f"node_id: str = new_label('{func}')")
        out(f"global node_id_by_checksum")
        out("nonlocal _state")
        out("nonlocal section_func")
        out()
        out(f"option_saved_state = save_state()")
        out()
        out("_output[node_id] = ''")
        implicit_go: bool = True
        for child in block.children:
            self.visit(child)
            if isinstance(child, Tree):
                if child.data == "goto_statement":
                    implicit_go = False
                    break
        if implicit_go:
            out(f"append_node: str = section_func()")
        else:
            out(f"append_node: str = go_function()")
        out("sha512: str = section + ' option ' + ' (' + state['world']['facing'].facing + ') ' + state_checksum()")
        out("if sha512 in node_id_by_checksum:")
        indent_inc()
        out("return node_id_by_checksum[sha512]")
        indent_dec()
        out("_output[node_id] += \"\\n\\n\" + _output[append_node]")

        out(f"restore_state(option_saved_state)")
        out(f"random.setstate(_state['random_state'])")
        out("return node_id")
        indent_dec()
        out()
        out(f"option_list.append((\"{basic_escape(option_description)}\", {func}))")
        out()

    def once_statement(self, tree: Tree):
        # out(f"# once: {self.__top_level_children(tree.children)}")
        self.once_counter += 1
        out(f"if {self.once_counter} not in _once:")
        indent_inc()
        out(f"_once.add({self.once_counter})")
        self.visit_children(tree)
        indent_dec()

    def once_else(self, tree: Tree):
        indent_dec()
        out("else:")
        indent_inc()

    def with_statement(self, tree: Tree):
        _ = ""

        with_item, block = tree.children

        for visit in self.visit(with_item):
            if visit:
                _ += visit

        func = self.next_func
        out(f"def {func}():")
        indent_inc()
        out(f"nonlocal {_}")
        out(f"_state = {_}")
        self.visit(block)
        indent_dec()

    def postfix_function_void(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def postfix_dot(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def postfix_expression(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def is_eq(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                if _:
                    _ += " "
                _ += visit
        return _

    def is_not_eq(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                if _:
                    _ += " "
                _ += visit
        return _

    def is_gt(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def is_lt(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def is_gte(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def is_lte(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def logical_and(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def and_op(self, tree: Tree):
        return " and "

    def logical_or(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def or_op(self, tree: Tree):
        return " or "

    def ternary_expression(self, tree: Tree):
        condition, if_true, if_false = tree.children
        _ = ""
        if isinstance(if_true, Tree):
            for visit in self.visit_children(if_true):
                if visit:
                    _ += visit
        if isinstance(if_true, Token):
            _ += if_true.strip()

        _ += " if "
        if isinstance(condition, Tree):
            for visit in self.visit_children(condition):
                if visit:
                    _ += visit
        if isinstance(condition, Token):
            _ += condition.strip()

        _ += " else "
        if isinstance(if_false, Tree):
            for visit in self.visit_children(if_false):
                if visit:
                    _ += visit
        if isinstance(if_false, Token):
            _ += if_false.strip()

        return _

    def boolean_value(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def boolean_true(self, tree: Tree):
        return "True"

    def boolean_false(self, tree: Tree):
        return "False"

    def assignment_statement(self, tree: Tree):
        postfix: Tree
        operator: Tree
        expression: Tree
        postfix, operator, expression = tree.children
        lvalue = self.visit(postfix)
        op = self.visit(operator)
        value = self.visit(expression)
        if lvalue == "state['world']":
            raise SyntaxError(f"Can not set world to a value. Only world members may be set.")
        out(f"{lvalue} {op} {value}")

    def assignment_operator(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def assignment_expression(self, tree: Tree) -> str:
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def type_specifier(self, tree: Tree) -> str:
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def primary_expression(self, tree: Tree) -> str:
        _ = f""
        for child in tree.children:
            if isinstance(child, Token):
                if child.type == "IDENTIFIER":
                    var = child.value
                    if var in self.scope_local:
                        _ += f"_local['{var}']"
                    elif var in self.scope_section:
                        _ += f"state[section_name]['vars']['{var}']"
                    elif var in self.scope_world:
                        _ += f"state['world']['{var}']"
                    else:
                        _ += f"state['world']['{var}']"
                else:
                    _ += child.value
            if isinstance(child, Tree):
                _ += self.visit(child)
        return _

    def string_constant(self, tree: Tree) -> str:
        return self.format_string(tree)

    def short_format_string(self, tree: Tree) -> str:
        return self.format_string(tree)

    def format_string(self, tree: Tree) -> str:
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        _ = textwrap.dedent(_)
        f = string.Formatter()
        params = f.parse(_)
        auto_format: list = [k for k in list(params) if k[1]]
        if auto_format:
            formatter: str = ".format("
            already: set[str] = set()
            key_var: set[str] = set()
            for lookup in auto_format:
                var: str = lookup[1]
                field_var: str = ''
                var = re.sub("(?i)^([a-z_][a-z_0-9]*).*", "\\1", var)
                if var in self.scope_local:
                    field_var = f"_local['{var}']"
                elif var in self.scope_section:
                    field_var = f"section['{var}']"
                elif var in self.scope_world:
                    field_var = var  # f"world['{var}']"
                    key_var.add(f"{var}=state['world']['{var}']")
                else:
                    key_var.add(f"{var}=state['world']['{var}']")

                if var not in already and field_var:
                    already.add(var)
                    _ = _.replace("{" + var, "{" + field_var)
            for kv in key_var:
                formatter += f"{kv}, "
            formatter += f"world=state['world'], section=state[section_name]['vars'])"
            _ += formatter
        return _

    def postfix_array(self, tree: Tree) -> str:
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def postfix_function_params(self, tree: Tree) -> str:
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def argument_expression_list(self, tree: Tree) -> str:
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def param_args(self, tree: Tree) -> str:
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return f"({_})"

    def param_void(self, tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return f"({_})"

    def comma(self, tree):
        return ", "

    def lbracket(self, tree):
        return "["

    def rbracket(self, tree):
        return "]"

    def conditional_expression(self, tree: Tree) -> str:
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def short_comment(self, tree: Tree):
        comment: str = tree.children[0]
        out(f"# {comment[1:].strip()}")

    def long_comment(self, tree: Tree):
        out()
        comment: str = tree.children[0]
        for line in comment[3:-3].strip().split("\n"):
            out(f"# {line}")
        out()

    def addition(self, tree: Tree) -> str:
        return self.__binary_op("+", tree)

    def subtraction(self, tree: Tree) -> str:
        return self.__binary_op("-", tree)

    def multiply(self, tree: Tree) -> str:
        return self.__binary_op("*", tree)

    def divide(self, tree: Tree) -> str:
        return self.__binary_op("/", tree)

    def int_divide(self, tree: Tree) -> str:
        return self.__binary_op("//", tree)

    def modulo(self, tree: Tree) -> str:
        return self.__binary_op("%", tree)

    def dice_roll(self, tree: Tree) -> str:
        explode = False
        tree_count, tree_die, tree_explode = tree.children
        _ = "int(dice.roll("
        _ += f"str({self.visit(tree_count)})"
        _ += " + \"d\" + "
        _ += f"str({self.visit(tree_die)})"
        if self.visit(tree_explode):
            _ += " + \"x\""
        _ += "))"
        return _

    def dice_explode(self, tree: Tree) -> bool:
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return True if _ else False

    def unary_cast(self, tree: Tree | Token):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

    def expression_positive(self, tree: Tree | Token):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return f"+{_}"

    def expression_negate(self, tree: Tree | Token):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return f"-{_}"

    def logical_not(self, tree: Tree | Token):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return f"not {_}"

    def __binary_op(self, op: str, tree: Tree) -> str:
        _ = ""
        left = tree.children[0]
        right = tree.children[1]
        if isinstance(left, Token):
            _ = left.value
        if isinstance(left, Tree):
            for part in self.visit(left):
                _ += part
        _ += f" {op} "
        if isinstance(right, Token):
            _ += right.value
        if isinstance(right, Tree):
            for part in self.visit(right):
                _ += part
        return _

    def paren_expression(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return f"({_})"

    def empty_statement(self, tree: Tree):
        return None

    def scope_statement(self, tree: Tree):
        scope, var, _ = tree.children
        out(f"# {scope} {var}")
        if scope == "world":
            self.scope_world.add(var)
        if scope == "section":
            self.scope_section.add(var)
        if scope == "local":
            self.scope_local.add(var)

    def __default__(self, tree: Tree | Token):
        out(f"# __default__: {tree.data}")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)
