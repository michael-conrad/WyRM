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
    compiled_program += ("    " * _indent) + text + "\n"


def end_section() -> None:
    out()
    out("for _ in option_list:")
    indent_inc()
    out("out += _[1]()")
    out("out += \"\\n\"")
    indent_dec()
    out()
    out(f"node_id: str = new_label()")
    out("_output[node_id] = out")
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

    @property
    def func_ctr(self) -> int:
        return self._func_ctr

    @property
    def next_func(self) -> str:
        self._func_ctr += 1
        return f"inner_{self._func_ctr:06}"

    @property
    def next_random_seed(self) -> int:
        self._next_random_seed += 1
        return self._next_random_seed

    def start(self, tree: Tree) -> str:
        _ = ""
        out("# START")
        out()

        # system required imports
        out("from goto import goto, label")
        out("import random")
        out("from jsonpickle import decode, encode")
        out("from types import SimpleNamespace")
        out("import types")
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

        import_block: list[str] = list()
        info_block: list[tuple[str, str]] = list()
        info_tags: set[str] = set()
        for child in tree.children:
            if isinstance(tree, Token):
                out(f"token: {tree.type} = {tree.value.strip()}")
                continue
            if child.data == "metadata_entry":
                tag, value, *_ = child.children
                if tag == "Library":
                    import_block.append(f"{value.strip()}")
                else:
                    if tag in info_tags:
                        raise SyntaxError(f"Duplicate entry {tag}. Each metadata entry must be uniquely tagged.")
                    info_tags.add(tag)
                    value: str = basic_escape(f"{value.strip()}")
                    info_block.append((tag.strip(), value))
        if import_block:
            out("# Imports from library metadata\n")
            out()
        for import_lib in import_block:
            out(f"import {import_lib}\n")
        if import_block:
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
        self.section_pad_length = len(str(len(tree.children)))

        # add the predefined dict, world, pointing to package locals
        out("# Sections")
        out(f"# pad: {self.section_pad_length}")
        out("")
        out("state: SimpleNamespace = SimpleNamespace()")
        out("state.world = SimpleNamespace()")
        out("state.world.turn = 0")
        out("state.world.facing = \"\"")
        out("state.world.location = \"\"")
        out("recurse_depth: int = 0")
        out()
        out("# Intentionally not tracked in state")
        out("_node_id: int = 0")
        out()
        out()
        out("def new_label() -> str:")
        indent_inc()
        out("global _node_id")
        out("_node_id += 1")
        out('return f"{_node_id:08x}"')
        indent_dec()
        out()
        out()
        out("_output: dict[str, str] = dict()")
        out()
        self.state_track_set.add('state')
        self.state_track_set.add('recurse_depth')

        # scan ahead for section names to build section to function lookup table

        for section_name_block in tree.find_data("section"):
            self.section_ctr += 1
            for child in section_name_block.children:
                if isinstance(child, Token):
                    name: str = child.value
                    section_name = f"section_{self.section_ctr:0{self.section_pad_length}}"
                    self.section_lookup[name] = section_name
                    self.section_ctr_lookup[name] = self.section_ctr

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

        out()
        out()
        out("def save_state() -> dict[str, str]:")
        indent_inc()
        for state in self.state_track_set:
            out(f"global {state}")
        out("states: dict[str, str] = dict()")
        for state in self.state_track_set:
            out(f"states['{state}'] = jsonpickle.encode({state})")
        out("return states")
        indent_dec()
        out()
        out()
        out("def restore_state(states: dict[str, str]) -> None:")
        indent_inc()
        for state in self.state_track_set:
            out(f"global {state}")
        for state in self.state_track_set:
            out(f"{state} = jsonpickle.decode(states['{state}'])")
        out("return")

    def section(self, tree: Tree):
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
                    # section_name = f"section_{self.section_ctr:0{self.section_pad_length}}"
                    self.section_lookup[name] = section_name
                    out(f"state.{section_name} = SimpleNamespace()")
                    out(f"state.{section_name}.name = \"{basic_escape(name)}\"")
                    out(f"state.{section_name}.id = {section_no}")
                    out(f"state.{section_name}.func_name = \"{section_name}\"")
                    out(f"state.{section_name}.metadata = dict()")
                    out(f"state.{section_name}.once = set()")
                    out(f"state.{section_name}.vars = dict()")
                    out()
                    out()
                    out(f"def {section_name}() -> str:")
                    indent_inc()
                    value: str = basic_escape(f"{name}")
                    out(f"{self.q3}{value}{self.q3}")
                    out()
                    out("global _output")
                    out("global state")
                    out("global recurse_depth")
                    out("recurse_depth += 1")
                    out("if recurse_depth > 10_000:")
                    out("    raise RecursionError()")
                    out(f"section: str = {self.q1}{value}{self.q1}")
                    out()
                    out(f"_state: SimpleNamespace = state.{section_name}")
                    out(f"_metadata: dict[str, str] = _state.metadata")
                    out(f"_once: set[int] = _state.once")
                    out(f"_vars: dict[str, any] = _state.vars")
                    self.once_counter += 1
                    out()
                    out(f"if {self.once_counter} not in _once:")
                    indent_inc()
                    out(f"_once.add({self.once_counter})")
                    out(f"state.{section_name}.random_state = random.Random({self.next_random_seed}).getstate()")
                    indent_dec()
                    out()
                    out("out: str = ''")
                    out(f"rand = random.Random()")
                    out(f"rand.setstate(state.{section_name}.random_state)")
                    out()
                    out("option_list: list[tuple[str, types.Callable]] = list()")
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
            out(f"out += \"\\n\\n\"")
            out(f"_ = {_}")
            out(f"out += str(_).rstrip()")
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

    def iteration_statement(self, tree: Tree):
        _ = ""
        out("# iteration")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

    def jump(self, tree: Tree):
        _ = ""
        out("# jump")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

    def comment(self, tree: Tree):
        _ = ""
        out("# comment")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

    def direction_statement(self, tree: Tree):
        _ = ""
        option_description = basic_unescape(tree.children[0][1:-1])
        section_name = "Start the Game"
        facing: str = ""
        if len(tree.children) == 2:
            section_name = option_description

        if len(tree.children) == 3:
            child = tree.children[1]
            if isinstance(child, Token):
                section_name = basic_unescape(tree.children[1][1:-1])
            if isinstance(child, Tree):
                if child.data == "facing":
                    facing = child.children[0]

        if len(tree.children) == 4:
            child = tree.children[1]
            if isinstance(child, Token):
                section_name = basic_unescape(tree.children[1][1:-1])
            child = tree.children[2]
            if isinstance(child, Tree):
                if child.data == "facing":
                    facing = child.children[0]

        if len(tree.children) > 4:
            out(f"# direction: {len(tree.children)} " + str(tree.children))

        if section_name not in self.section_lookup:
            raise KeyError(f"Section {section_name} not found.\n"
                           f"Valid sections: {[k for k in self.section_lookup.keys()]}")

        section_func: str = self.section_lookup[section_name]

        func: str = self.next_func
        out()
        out(f"# direction statement")
        out(f"def {func}() -> str:")
        indent_inc()
        out(f"\"\"\"{basic_escape(option_description)}\"\"\"")
        out("nonlocal out")
        out("nonlocal rand")
        out(f"saved_state = save_state()")
        if facing:
            out(f"state.world.facing = {facing}")
        out(f"destination_node: str = {section_func}()")
        out(f"restore_state(saved_state)")
        out(f"rand.setstate(_state.random_state)")
        d: str = ""
        d += "return f\""
        d += f"<a href=\\{self.q1}"
        d += "{destination_node}"
        d += f".html\\{self.q1}>"
        d += html.escape(option_description).strip()
        d += '</a>"'
        out(d)
        indent_dec()
        out()
        out(f"option_list.append((\"{basic_escape(option_description)}\", {func}))")
        out()

    def option_statement(self, tree: Tree):
        _ = ""
        option_description = basic_unescape(tree.children[0][1:-1])

        func: str = self.next_func
        out()
        out(f"# option statement")
        out(f"def {func}() -> str:")
        indent_inc()
        out(f"\"\"\"{basic_escape(option_description)}\"\"\"")
        out("nonlocal out")
        out("nonlocal rand")
        out(f"saved_state = save_state()")
        out()
        self.visit(tree.children[1])
        out()
        out(f"restore_state(saved_state)")
        out(f"rand.setstate(_state.random_state)")
        indent_dec()
        out()
        out(f"option_list.append((\"{basic_escape(option_description)}\", {func}))")
        out()

    def once_statement(self, tree: Tree):
        _ = ""
        out("# once")
        self.once_counter += 1
        out()
        out(f"if {self.once_counter} not in _once:")
        indent_inc()
        out(f"_once.add({self.once_counter})")
        out()
        self.visit_children(tree)
        out(_)
        indent_dec()

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

    def with_item(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        out(f"# with item: {_}")
        return _

    def library_statement(self, tree: Tree):
        out("# library")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

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
                _ += visit
        return _

    def is_not_eq(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
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
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)

    def assignment_operator(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return " " + _ + " "

    def assignment_expression(self, tree: Tree) -> str:
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
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

    def modulo(self, tree: Tree) -> str:
        return self.__binary_op("%", tree)

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

    def __default__(self, tree: Tree | Token):
        _ = ""
        out(f"# __default__: {tree.data}")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _:
            out(_)
