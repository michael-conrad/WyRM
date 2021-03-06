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


class GamebookCompiler(lark.visitors.Interpreter):
    q1 = "\""
    q3 = "\"\"\""

    once_counter: int = 0
    room_ctr: int = 0
    room_pad_length: int = 1
    state_track_set: set[str] = set()
    _func_ctr: int = 0
    _abort_ctr: int = 0

    room_lookup: dict[str, str] = dict()
    room_ctr_lookup: dict[str, int] = dict()
    var_lookup: dict[str, str] = dict()

    _next_random_seed: int = 0

    main_room: str | None = None

    import_block: list[str] = list()

    scope_world: set[str] = set()
    scope_room: set[str] = set()
    scope_local: set[str] = set()
    defined_macros: dict[str, Tree] = dict()

    next_option_ctrs: dict[str, int] = dict()

    macro_preexec: str = ""
    macro_postexec: str = ""

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
    def next_abort(self) -> str:
        self._abort_ctr += 1
        return f"abort_{self._abort_ctr:06x}"

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
        # system required imports
        out("from contextlib import contextmanager")
        out("from datetime import datetime")
        out("import re")
        out("import shutil")
        out("import os")
        out("import html")
        out("import dice")
        out("import hashlib")
        out("import random")
        out("import jsonpickle")
        out("from collections.abc import Callable")
        out("import textwrap")
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

    def metadata(self, tree: Tree):
        self.visit_children(tree)

    def metadata_entries(self, tree: Tree):
        info_block: list[tuple[str, str]] = list()
        info_tags: set[str] = set()
        self.visit_children(tree)
        for tag, value in self.visit_children(tree):
            if tag == "Library":
                self.import_block.append(f"{value.strip()}")
            else:
                if tag in info_tags:
                    raise SyntaxError(f"Duplicate entry {tag}. Each metadata entry must be uniquely tagged.")
                info_tags.add(tag)
                value: str = basic_escape(f"{value.strip()}")
                info_block.append((tag.strip(), value))

        if info_block:
            out("gamebook_metadata: dict[str, str] = dict()")
        for tag, value in info_block:
            out(f"gamebook_metadata[\"{tag}\"] = \"{value}\"")
            if tag == "preexec":
                self.macro_preexec = value.strip()
            if tag == "postexec":
                self.macro_postexec = value.strip()
        out()

    def metadata_entry(self, tree: Tree | Token) -> tuple[str, str]:
        tag: Token
        value: Token
        tag, value, *_ = tree.children
        return tag.strip(), value.strip()

    def rooms(self, tree: Tree):
        # always import the gamebook core module
        if "gamebook_core" not in self.import_block:
            self.import_block.append("gamebook_core")
        if self.import_block:
            self.import_block.sort()
        for import_lib in self.import_block:
            out(f"import {import_lib}")
        out()
        for import_lib in self.import_block:
            out(f"from {import_lib} import *")
        out()

        self.room_pad_length = len(str(len([s for s in tree.find_data("room")])))

        imports = dict()
        for _ in self.import_block:
            exec(f'import {_}', imports)
            exec(f'from {_} import *', imports)
        for attr in [*imports]:
            self.scope_world.add(attr)


        # enable proper use of "goto" to terminate all remaining code in a room
        # see: https://stackoverflow.com/a/3171971/12407701
        out()
        out("class NestedBreakException(Exception):")
        indent_inc()
        out("pass")
        indent_dec()
        out()
        out()
        out("@contextmanager")
        out("def nested_break():")
        indent_inc()
        out('"""\nEnable proper use of "goto" to terminate all remaining code in a room.\nSee: '
            'https://stackoverflow.com/a/3171971/12407701\n"""')
        out()
        out("try:")
        indent_inc()
        out("yield NestedBreakException()")
        indent_dec()
        out("except NestedBreakException as e:")
        indent_inc()
        out("pass")
        indent_dec()
        indent_dec()
        out()
        out()

        # add the predefined dict, world, pointing to package locals
        out("state: dict[str, any] = dict()")
        out("state['world'] = dict()")
        out("recurse_depth: int = 0")
        out("imports = dict()")
        out()
        for _ in self.import_block:
            out(f"exec('from {_} import *', imports)")
        out()
        out(f"for attr in [*imports]:")
        indent_inc()
        out(f"state['world'][attr] = imports[attr]")
        indent_dec()
        out("ignore_pickle_keys: set[str] = set()")
        out(f"for attr in [*imports]:")
        indent_inc()
        out(f"ignore_pickle_keys.add(attr)")
        indent_dec()
        out(f"ignore_pickle_keys.add('__builtins__')")
        out()
        self.scope_world.add("facing")
        out("state['world']['facing'] = state['world']['Facing']().with_facing('n')")
        out()
        out("_node_id: dict[str, int] = dict()")
        out()
        out()
        out("def copy(o: any) -> any:")
        indent_inc()
        out("return jsonpickle.decode(jsonpickle.encode(any, keys=True), keys=True)")
        indent_dec()
        out()
        out()
        out("def face(facing: str):")
        indent_inc()
        out("global state")
        out("state['world']['facing'].face(facing)")
        indent_dec()
        out()
        out()
        out("def new_label(room: str = 'no-room') -> str:")
        indent_inc()
        out("global _node_id")
        out("if room not in _node_id:")
        indent_inc()
        out("_node_id[room]=0")
        indent_dec()
        out("_node_id[room] += 1")
        out("cnt: int = _node_id[room]")
        out('return f"{room}-{cnt:03x}"')
        indent_dec()
        out()
        out()
        out("_output: dict[str, str] = dict()")
        out("_output_post_append: dict[str, str] = dict()")
        out("node_id_by_hash: dict[str, str] = dict()")
        out()
        out(f"state['world']['__builtins__'] = globals()['__builtins__']")
        out()

        # scan ahead for room names to build room to function lookup table

        for child in tree.find_data("room"):
            if isinstance(child, Token):
                continue
            if isinstance(child, Tree):
                if child.data == "room":
                    room_name_block = child
                    self.room_ctr += 1
                    room = room_name_block.children[0]
                    if isinstance(room, Token):
                        name: str = room.value
                        if name in self.room_lookup:
                            raise SyntaxError(f"Room {name} is duplicated")
                        room_name = f"room_{self.room_ctr:0{self.room_pad_length}}"
                        self.room_lookup[name] = room_name
                        self.room_ctr_lookup[name] = self.room_ctr
                        if not self.main_room:
                            self.main_room = name

        _ = ""
        for child in tree.children:
            if isinstance(child, Token):
                out(child.value)
            if isinstance(child, Tree):
                _c = self.visit(child)
                if _c:
                    for _d in _c:
                        _ += _d
        if _.strip():
            out(_)

        # make sure last room function has closing code
        self.end_room()
        out("room_function_lookup: dict[str, Callable] = dict()")
        for _key in self.room_lookup.keys():
            _function = self.room_lookup[_key]
            out(f"room_function_lookup[\"{_key}\"] = {_function}")

        out()
        out()
        out("def state_checksum() -> str:")
        indent_inc()
        out("pickled: str = save_state()")
        out("node_hash: str = hashlib.sha512(pickled.encode('utf-8')).hexdigest()")
        out("return node_hash")
        indent_dec()
        out()
        out()
        out("def save_state() -> str:")
        indent_inc()
        sorted_track = sorted(self.state_track_set)
        out("saved_states: dict[str, dict | str] = dict()")
        out("saved_states['world_vars']: dict[str, any] = dict()")
        out("for var in state['world'].keys():")
        indent_inc()
        out("if var in ignore_pickle_keys:")
        indent_inc()
        out("continue")
        indent_dec()
        out("saved_states['world_vars'][var] = state['world'][var]")
        indent_dec()
        for state in sorted_track:
            out(f"saved_states['{state}'] = state['{state}']")
        out("return jsonpickle.encode(saved_states, keys=True)")
        indent_dec()
        out()
        out()
        out("def restore_state(_saved_states: str) -> None:")
        indent_inc()
        out("saved_states = jsonpickle.decode(_saved_states, keys=True)")
        out("for var in saved_states['world_vars'].keys():")
        indent_inc()
        out("state['world'][var] = saved_states['world_vars'][var]")
        indent_dec()
        for state in sorted_track:
            out(f"state['{state}'] = saved_states['{state}']")
        out("return")
        indent_dec()

        # the first room is 'main'
        out()
        out()
        out(f"index_node: str = {self.room_lookup[self.main_room]}()")
        out("""
import mdformat
md_options: dict[str, any] = dict()
md_options["wrap"] = 80

shutil.rmtree("md", ignore_errors=True)
os.makedirs("md", exist_ok=True)

for append_to in _output_post_append:
    append_from: str = _output_post_append[append_to]
    _output[append_to] += '\\n\\n' + _output[append_from]
    
for key in _output:
    out = mdformat.text(_output[key], options=md_options)
    with open("md/" + key + ".md", "w") as w:
        w.write("\\n")
        w.write(out)
        w.write("\\n")
        
with open("md/index.md", "w") as w:
    out = mdformat.text(_output[index_node], options=md_options)
    w.write("\\n")
    w.write(out)
    w.write("\\n")
    
with open("index.md", "w") as w:
    out = mdformat.text(_output[index_node], options=md_options)
    out = re.sub("\((.*?md)\)", "(md/\\\\1)", out)
    w.write("\\n")
    w.write(out)
    w.write("\\n")

""")

    def room(self, tree: Tree):

        # always clear non-world scopes at start of processing a new room
        self.scope_room.clear()
        self.scope_room.add("items")

        self.scope_local.clear()

        _ = ""
        for child in tree.children:
            if isinstance(child, Tree):
                self.visit(child)
                continue
            if isinstance(child, Token):
                if child.type == "ROOM_NAME":
                    name = child.strip()
                    room_name: str = self.room_lookup[name]
                    room_no: int = self.room_ctr_lookup[name]
                    # always make sure previous room has correct return code
                    if room_no > 1:
                        self.end_room()
                    self.scope_room.add("items")
                    self.room_lookup[name] = room_name
                    self.state_track_set.add(room_name)
                    out(f"state['{room_name}'] = dict()")
                    out(f"state['{room_name}']['once'] = set()")
                    out(f"state['{room_name}']['vars'] = dict()")
                    out(f"state['{room_name}']['vars']['items'] = gamebook_core.Items()")
                    out(f"state['{room_name}']['random_state'] = random.Random({self.next_random_seed}).getstate()")
                    out()
                    out()

                    out(f"def {room_name}() -> str:")
                    indent_inc()
                    value: str = basic_escape(f"{name}")
                    out(f"{self.q3}{value}{self.q3}")
                    out("global _output")
                    out("global state")
                    out("global recurse_depth")
                    out()
                    out(f"_sub_func_counter: int = 0")
                    out(f"_state: dict[str, any] = state['{room_name}']")
                    out(f"_once: set[int] = _state['once']")
                    out(f"room: str = {self.q1}{value}{self.q1}")
                    out(f"room_name: str = {self.q1}{room_name}{self.q1}")
                    out("global node_id_by_hash")
                    out("node_hash: str = room_name + state_checksum()")
                    out("if node_hash in node_id_by_hash:")
                    indent_inc()
                    out("return node_id_by_hash[node_hash]")
                    indent_dec()
                    out(f"node_id: str = new_label(room_name)")
                    out("node_id_by_hash[node_hash] = node_id")
                    out()
                    out("next_turn()")
                    out()
                    out("if turn() % 10 == 0 or True:")
                    indent_inc()
                    out("_ = str(datetime.now().time())[:8]")
                    out("")
                    out("print(f'Turn: {turn()} [{_}] {room}')")
                    indent_dec()
                    out()
                    out("out = ''")
                    out(f"room_func: Callable = {room_name}")
                    out("recurse_depth += 1")
                    out("if recurse_depth > 1000:")
                    indent_inc()
                    out("raise RecursionError()")
                    indent_dec()
                    out(f"random.setstate(_state['random_state'])")
                    out("option_list: list[tuple[str, Callable]] = list()")
                    out("with nested_break() as abort_processing:")
                    indent_inc()
                    if self.macro_preexec:
                        if self.macro_preexec in self.defined_macros:
                            self.visit(self.defined_macros[self.macro_preexec])
                    continue
                if child.type == "NEWLINE":
                    continue
                out(f"Unknown token: {child.type} = {child.value}")
                continue

            return _

    def statement(self, tree: Tree) -> None:
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)

    def labeled_statement(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)

    def compound_statement(self, tree: Tree):
        label: str = self.next_abort
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)

    def block_item_list(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)

    def block_item(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)

    def expression_statement(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(f"rvalues: any = {_.rstrip()}")
            out("if rvalues is not None:")
            indent_inc()  # 1
            out(f"if not isinstance(rvalues, list):")
            indent_inc()  # 2
            out("rvalues = [rvalues]")
            indent_dec()  # 2
            out()
            out("for rvalue in rvalues:")
            indent_inc()  # 2
            out("if isinstance(rvalue, gamebook_core.AbstractItem):")
            indent_inc()  # 3
            out("state[room_name]['vars']['items'].add(rvalue)")
            indent_dec()  # 2
            out("elif isinstance(rvalue, gamebook_core.AbstractCharacter):")
            indent_inc()  # 3
            out("state[room_name]['vars']['items'].add(rvalue)")
            indent_dec()  # 2
            out("elif rvalue is not None:")
            indent_inc()  # 3
            out(f"out += \"\\n\\n\"")
            # out(f"_ = html.escape(str(segment))")
            out(f"out += textwrap.dedent(str(rvalue))")
            indent_dec()  # 2
            indent_dec()  # 1
            indent_dec()  # 0

    def selection_statement(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)

    def __top_level_children(self, children: list[Tree, Token] | Tree) -> str:
        _ = ""

        if isinstance(children, Tree):
            children = children.children

        for child in children:
            if isinstance(child, Token):
                if _.strip():
                    _ += ", "
                _ += f"token: {child.type}"
            if isinstance(child, Tree):
                if _.strip():
                    _ += ", "
                _ += f"tree: {child.data}"
        return _

    def if_else_statement(self, tree: Tree):
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
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)

    # while_statement:  WHILE "(" expression ")" statement
    def while_statement(self, tree: Tree):
        _, expression, statement = tree.children
        e = self.visit(expression)
        out(f"while {e}:")
        indent_inc()
        self.visit(statement)
        indent_dec()

    # do_while_statement: DO statement WHILE "(" expression ")" _eos
    def do_while_statement(self, tree: Tree):
        _, compound_statement, _, assignment_express, _ = tree.children
        out("while True:")
        indent_inc()
        self.visit(compound_statement)
        e = self.visit(assignment_express)
        out(f"if {e}:")
        indent_inc()
        out("continue # continue do while loop")
        indent_dec()
        out("break  # exit do while loop")
        indent_dec()

    # for_statement: FOR "(" assignment_statement expression_statement expression ")" statement
    def for_statement(self, tree: Tree):
        _, assignment_expression, expression_statement, assignment_express, compound_statement = tree.children
        out(self.visit(assignment_expression))
        es = self.visit(expression_statement)
        ae = self.visit(assignment_express)

        out(f"while True:")
        indent_inc()
        out(f"_ = {es}")
        out(f"if not _:")
        indent_inc()
        out("break  # exit for loop")
        indent_dec()

        self.visit(compound_statement)

        out(f"{ae}")
        indent_dec()

    # for_each_statement: FOR "(" IDENTIFIER ":" expression")" statement
    def for_each_statement(self, tree: Tree):
        postfix: Tree
        expression: Tree
        compound_statement: Tree
        _, postfix, expression, compound_statement = tree.children

        lvalue: str = self.visit(postfix)
        if lvalue == "state['world']":
            raise SyntaxError(f"Can not set world to a value. Only world members may be set.")
        saved_locals = self.scope_local.copy()
        if lvalue.startswith("state['world']['"):
            var = lvalue[len("state['world']['"):]
            var = var[:var.index("'")]
            if var not in self.scope_world and var not in self.scope_room:
                self.scope_local.add(var)

        out(f"for {self.visit(postfix)} in {self.visit(expression)}:")
        indent_inc()
        self.visit(compound_statement)
        indent_dec()
        self.scope_local.intersection_update(saved_locals)

    def repeat_statement(self, tree: Tree):
        _, expression, statement = tree.children

        e = self.visit(expression)
        out(f"for _ in range({e}):")
        indent_inc()
        self.visit(statement)
        indent_dec()

    def jump_statement(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)

    def clear_options(self, tree: Tree):
        self.visit_children(tree)
        out("option_list.clear()")

    def goto_statement(self, tree: Tree):
        _, new_room, direction_facing, *_ = tree.children
        func = self.next_goto
        out()
        out(f"def {func}():")
        indent_inc()
        out("global room_function_lookup")
        out("global node_id_by_hash")
        out("nonlocal _state")
        out("nonlocal node_id")
        out("nonlocal _sub_func_counter")
        out()
        out("_sub_func_counter += 1")
        out(f"node_hash: str = '{func}' + str(_sub_func_counter) + state_checksum()")
        out("if node_hash in node_id_by_hash:")
        indent_inc()
        out("return node_id_by_hash[node_hash]")
        indent_dec()
        out()
        out(f"goto_saved_state = save_state()")

        room: str = ""
        for _ in self.visit(new_room):
            room += _
        out(f"lookup: str = str({room})")
        out(f"if lookup not in room_function_lookup:")
        indent_inc()
        out(f"raise KeyError(f\"room {{lookup}} not found.\")")
        indent_dec()
        facing = ""
        for _ in self.visit_children(direction_facing):
            facing += _
        out(f"state['world']['facing'].face({facing})")

        out(f"append_node: str = room_function_lookup[lookup]()")
        out(f"node_id_by_hash[node_hash] = append_node")
        out(f"restore_state(goto_saved_state)")
        out(f"random.setstate(_state['random_state'])")
        out(f"return append_node")
        indent_dec()
        out(f"append_node: str = {func}()")
        out("_output_post_append[node_id] = append_node")
        out("raise abort_processing # end processing after goto")
        return None

    def comment(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)

    def direction_statement(self, tree: Tree):
        short_format_string, direction_room, direction_facing, _ = tree.children

        option_bin_description: str = ""
        for child in short_format_string.children:
            if isinstance(child, Token):
                option_bin_description += child.value
        option_bin_description = eval(option_bin_description)

        option_description = ""
        _ = self.visit(short_format_string)
        if _.strip():
            option_description += _

        room_name = ""
        for _ in self.visit_children(direction_room):
            if _.strip():
                room_name += _
        room_name = room_name.strip()[1:-1]

        facing = ""
        for _ in self.visit_children(direction_facing):
            facing += _

        if room_name not in self.room_lookup:
            print(self.__top_level_children(tree.children))
            raise KeyError(f"Room {room_name} not found.\n"
                           f"Valid rooms: {[k for k in self.room_lookup.keys()]}")

        room_func: str = self.room_lookup[room_name]

        func: str = self.next_direction
        out()
        out(f"def {func}() -> str:")
        indent_inc()
        out(f"\"\"\"{basic_escape(option_bin_description)}\"\"\"")
        out()
        out("global node_id_by_hash")
        out("nonlocal out")
        out("nonlocal room")
        out("nonlocal _sub_func_counter")
        out()
        out("_sub_func_counter += 1")
        out(f"direction_node_hash: str = '{func}' + str(_sub_func_counter) + state_checksum()")
        out("if direction_node_hash in node_id_by_hash:")
        indent_inc()
        out("return node_id_by_hash[direction_node_hash]")
        indent_dec()
        out()
        out(f"state['world']['facing'].face({facing})")
        out()
        out(f"direction_node_id: str = {room_func}()")

        out("node_id_by_hash[direction_node_hash] = direction_node_id")
        out()
        out(f"return direction_node_id")
        indent_dec()
        out(f"option_list.append(({option_description}, {func}))")

    def option_statement(self, tree: Tree):
        next_option_ctrs = self.next_option_ctrs
        _ = ""
        block: Tree = tree.children[1]
        option_description = self.visit(tree.children[0])  # basic_unescape(tree.children[0][1:-1])
        func: str = self.next_option
        saved_locals = self.scope_local.copy()
        closures: str = ""
        if self.scope_local:
            out()
            out(f"# Closure vars: {self.scope_local}")
            for var in self.scope_local:
                out(f"_local_{var} = _local_{var} if '_local_{var}' in locals() else False")

            # out()
            for var in self.scope_local:
                out(f"_o_{var} = _local_{var}")
            out()
            for var in self.scope_local:
                if closures:
                    closures += ", "
                closures += f"_local_{var}=_o_{var}"
        out(f"def {func}({closures}) -> str:")
        indent_inc()
        out(f"\"\"\"{basic_escape(option_description)}\"\"\"")
        # out()
        out("global node_id_by_hash")
        out("global _output")
        out("nonlocal _state")
        out("nonlocal room_func")
        out("nonlocal _sub_func_counter")
        out()
        out("_sub_func_counter += 1")
        out(f"node_hash: str = '{func}' + str(_sub_func_counter) + state_checksum()")
        out("if node_hash in node_id_by_hash:")
        indent_inc()
        out("return node_id_by_hash[node_hash]")
        indent_dec()
        out(f"option_saved_state = save_state()")
        out()
        out(f"node_id: str = new_label('{func}')")
        out("node_id_by_hash[node_hash] = node_id")
        out()
        out("with nested_break() as abort_processing:")
        indent_inc()
        out("out = ''")
        self.visit(block)
        out(f"append_node: str = room_func()")
        out("_output_post_append[node_id] = append_node")
        indent_dec()
        out(f"restore_state(option_saved_state)")
        out(f"random.setstate(_state['random_state'])")
        out("_output[node_id] = out")
        out("return node_id")
        indent_dec()
        out(f"option_list.append(({option_description}, {func}))")
        self.scope_local.intersection_update(saved_locals)

    def once_statement(self, tree: Tree):
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

    def macro_define(self, tree: Tree) -> None:
        macro_id_tree, compound_statement = tree.children
        macro_id: str = ""
        for _ in self.visit(macro_id_tree):
            macro_id += _
        if macro_id in self.defined_macros:
            raise Exception(f"Macro {macro_id} previously defined. Macros can only be defined once.")
        self.defined_macros[macro_id] = compound_statement

    def macro_invoke(self, tree: Tree) -> None:
        macro_id_tree, _ = tree.children
        macro_id: str = ""
        for _ in self.visit(macro_id_tree):
            macro_id += _
        if macro_id not in self.defined_macros:
            raise Exception(f"Macro {macro_id} not defined.")
        self.visit(self.defined_macros[macro_id])

    def macro_id(self, tree: Tree) -> any:
        return self.visit_children(tree)


    def python_list(self, tree: Tree):
        _ = "list("
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        _ += ")"
        return _

    def python_tuple(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return _

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
                if _.strip():
                    _ += " "
                _ += visit
        return _

    def is_not_eq(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                if _.strip():
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
        postfix, operator, expression, _ = tree.children
        lvalue: str = self.visit(postfix)
        op: str = self.visit(operator)
        value: str = self.visit(expression)
        if lvalue == "state['world']":
            raise SyntaxError(f"Can not set world to a value. Only world members may be set.")
        if lvalue.startswith("state['world']['"):
            var = lvalue[len("state['world']['"):]
            var = var[:var.index("'")]
            if var not in self.scope_world:
                self.scope_local.add(var)
                lvalue: str = self.visit(postfix)
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
                    if var in __builtins__:
                        _ += f"__builtins__.{var}"
                    elif var in self.scope_local:
                        _ += f"_local_{var}"
                    elif var in self.scope_room:
                        _ += f"state[room_name]['vars']['{var}']"
                    elif var in self.scope_world:
                        _ += f"state['world']['{var}']"
                    else:
                        _ += f"_local_{var}"
                        self.scope_local.add(var)
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
                    field_var = var
                    key_var.add(f"{var}=_local_{var}")
                elif var in self.scope_room:
                    field_var = var
                    key_var.add(f"{var}=state[room_name]['vars']['{var}']")
                elif var in self.scope_world:
                    field_var = var
                    key_var.add(f"{var}=state['world']['{var}']")
                else:
                    field_var = var
                    key_var.add(f"{var}=state['world']['{var}']")

                if var not in already and field_var:
                    already.add(var)
                    _ = _.replace("{" + var, "{" + field_var)
            do_comma: bool = False
            for kv in key_var:
                if do_comma:
                    formatter += ", "
                else:
                    do_comma = True
                formatter += f"{kv}"
            formatter += f")"
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

    def list_args(self, tree: Tree) -> str:
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        return f"({_})"

    def list_void(self, tree):
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
        comment: str = tree.children[0]
        for line in comment[3:-3].strip().split("\n"):
            out(f"# {line}")

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
        tree_count, tree_die, tree_explode = tree.children
        _ = "dice_roll("
        _ += f"int({self.visit(tree_count)})"
        _ += ", "
        _ += f"int({self.visit(tree_die)})"
        if self.visit(tree_explode):
            _ += ", explode=True"
        _ += ")"
        return _

    # max_dice_roll: "max" unary_expression "@" unary_expression dice_explode
    def max_dice_roll(self, tree: Tree) -> str:
        tree_count, tree_die, tree_explode = tree.children
        _ = f"int({self.visit(tree_count)})"
        _ += " * "
        _ += f"int({self.visit(tree_die)})"
        return _

    # min_dice_roll: "min" unary_expression "@" unary_expression dice_explode
    def min_dice_roll(self, tree: Tree) -> str:
        tree_count, tree_die, tree_explode = tree.children
        _ = f"int({self.visit(tree_count)})"
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
        if scope == "world":
            self.scope_world.add(var)
            out(f"if '{var}' not in state['world']:")
            indent_inc()
            out(f"state['world']['{var}'] = False")
            indent_dec()
        if scope == "room":
            self.scope_room.add(var)
            out(f"if '{var}' not in state[room_name]['vars']:")
            indent_inc()
            out(f"state[room_name]['vars']['{var}'] = False")
            indent_dec()
        if scope == "local":
            self.scope_local.add(var)
            out(f"_local_{var}: any = False")

    def start_over(self, tree: Tree):
        out(f"def start_over():")
        indent_inc()
        out("return 'index'")
        indent_dec()

        out(f"option_list.append((\"Start Over\", start_over))")
        out("raise abort_processing # end processing after restart statement")

    def __default__(self, tree: Tree | Token):
        out(f"# __default__: {tree.data}")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)

    def end_room(self) -> None:
        if self.macro_postexec:
            if self.macro_postexec in self.defined_macros:
                self.visit(self.defined_macros[self.macro_postexec])
        out("out += state[room_name]['vars']['items'].inv")
        out("out += \"\\n\\n\"")
        indent_dec()
        out(f"_state['random_state'] = random.getstate()")
        out("recurse_depth -= 1")
        out("option_list.sort(key=lambda x: x[0])")
        out("saved_state = save_state()")

        out("if option_list:")
        indent_inc()
        out("out += \"\\n_____\\n\"")
        out("for _ in option_list:")
        indent_inc()
        out("destination_node = _[1]()")
        out("restore_state(saved_state)")
        out(f"_option_text: str = str(_[0])")
        out(f"_option_text = html.escape(_option_text)")
        out(f"_md_link: str = \"[\" + _option_text + \"](\" + destination_node + \".md)\"")
        out("out += \"* \" + _md_link")
        out("out += \"\\n\"")
        indent_dec()
        out("out += \"_____\\n\"")
        indent_dec()

        out("restore_turn()")
        out("_output[node_id] = out")
        out("return node_id")
        indent_dec()
        out()
        out()
