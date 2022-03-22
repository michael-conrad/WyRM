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


def end_room() -> None:
    out("break  # end room")
    indent_dec()
    out("recurse_depth -= 1")
    out("out += state[room_name]['vars']['items'].inv")
    out("out += \"\\n\\n\"")
    out("option_list.sort(key=lambda x: x[0])")
    out("for _ in option_list:")
    indent_inc()
    out("saved_state = save_state()")
    out("destination_node = _[1]()")
    out("restore_state(saved_state)")
    out(f"_option_text: str = str(_[0])")
    out(f"_option_text = html.escape(_option_text)")
    out(f"_md_link: str = \"[\" + _option_text + \"](\" + destination_node + \")\"")
    out("out += \"* \" + _md_link")
    out("out += \"\\n\"")
    indent_dec()
    out("restore_turn()")
    out("_output[node_id] = out")
    out("return node_id")
    indent_dec()
    out()
    out()


class GamebookCompiler(lark.visitors.Interpreter):
    q1 = "\""
    q3 = "\"\"\""

    once_counter: int = 0
    room_ctr: int = 0
    room_pad_length: int = 1
    state_track_set: set[str] = set()
    _func_ctr: int = 0

    room_lookup: dict[str, str] = dict()
    room_ctr_lookup: dict[str, int] = dict()
    var_lookup: dict[str, str] = dict()

    _next_random_seed: int = 0

    main_room: str | None = None

    import_block: list[str] = list()

    scope_world: set[str] = set()
    scope_room: set[str] = set()
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

        # system required imports
        out("import re")
        out("from gamebook_core import *")
        out("import shutil")
        out("import os")
        out("import html")
        out("import dice")
        out("import hashlib")
        out("import random")
        out("import jsonpickle")
        out("from collections.abc import Callable")

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
        out("# Metadata entries")
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

        if self.import_block:
            out("# Imports from library metadata\n")
        for import_lib in self.import_block:
            out(f"from {import_lib} import *\n")
        out()

        if info_block:
            out("# Game Book Metadata\n")
            out("gamebook_metadata: dict[str, str] = dict()\n")
        for tag, value in info_block:
            out(f"gamebook_metadata[\"{tag}\"] = \"{value}\"\n")
        out()

    def metadata_entry(self, tree: Tree | Token) -> tuple[str, str]:
        tag: Token
        value: Token
        tag, value, *_ = tree.children
        return tag.strip(), value.strip()

    def rooms(self, tree: Tree):
        self.room_pad_length = len(str(len([s for s in tree.find_data("room")])))

        # add the predefined dict, world, pointing to package locals
        out("# Rooms")
        out("repeat_state_tracking: dict[str, str] = dict()")
        out("state: dict[str, any] = dict()")
        out("state['world'] = dict()")
        out("recurse_depth: int = 0")
        out("imports = dict()")
        if "gamebook_core" not in self.import_block:
            self.import_block.append("gamebook_core")
        for _ in self.import_block:
            out(f"exec('from {_} import *', imports)")
        out(f"for attr in [*imports]:")
        indent_inc()
        out(f"state['world'][attr] = imports[attr]")
        indent_dec()
        out("state['world']['facing'] = state['world']['Facing']().with_facing('n')")
        out("# build up list of keys not to pickle or checksum")
        out("ignore_pickle_keys: set[str] = set()")
        out(f"for attr in [*imports]:")
        indent_inc()
        out(f"ignore_pickle_keys.add(attr)")
        indent_dec()
        out(f"ignore_pickle_keys.add('__builtins__')")
        out("# Intentionally not tracked in state")
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
        end_room()
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
shutil.rmtree("md", ignore_errors=True)
os.makedirs("md", exist_ok=True)
for append_to in _output_post_append:
    append_from: str = _output_post_append[append_to]
    _output[append_to] += '\\n\\n' + _output[append_from]
for key in _output:
    out = _output[key]
    out = re.sub("\\n\\\\s+\\n", "\\n\\n", out) 
    with open("md/" + key + ".md", "w") as w:
        w.write("\\n")
        # w.write("# " + key)
        w.write(out)
        w.write("\\n")
        
with open("md/index.md", "w") as w:
    out = _output[index_node]
    out = re.sub("\\n\\\\s+\\n", "\\n\\n", out)
    w.write("\\n")
    # w.write("# " + index_node)
    w.write(out)
    w.write("\\n")        
""")

    def room(self, tree: Tree):

        # always clear non-world scopes at start of processing a new room
        self.scope_room.clear()
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
                        end_room()
                    self.room_lookup[name] = room_name
                    self.state_track_set.add(room_name)
                    out(f"state['{room_name}'] = dict()")
                    out(f"state['{room_name}']['name'] = \"{basic_escape(name)}\"")
                    out(f"state['{room_name}']['id'] = {room_no}")
                    out(f"state['{room_name}']['func_name'] = \"{room_name}\"")
                    out(f"state['{room_name}']['metadata'] = dict()")
                    out(f"state['{room_name}']['once'] = set()")
                    out(f"state['{room_name}']['vars'] = dict()")
                    out(f"state['{room_name}']['vars']['items'] = gamebook_core.Items()")
                    out()
                    out()

                    out(f"def {room_name}() -> str:")
                    indent_inc()
                    value: str = basic_escape(f"{name}")
                    out(f"{self.q3}{value}{self.q3}")
                    out("global _output")
                    out("global state")
                    out("global recurse_depth")
                    out(f"_state: dict[str, any] = state['{room_name}']")
                    out(f"_once: set[int] = _state['once']")
                    out(f"room: str = {self.q1}{value}{self.q1}")
                    out(f"room_name: str = {self.q1}{room_name}{self.q1}")
                    out("# see if this is a repeating state, if yes, just use original node id")
                    out("global node_id_by_hash")
                    out("node_hash: str = room_name + state_checksum()")
                    out("if node_hash in node_id_by_hash:")
                    indent_inc()
                    out("return node_id_by_hash[node_hash]")
                    indent_dec()
                    out(f"node_id: str = new_label(room_name)")
                    out("next_turn()")
                    out("out = ''")
                    out("node_id_by_hash[node_hash] = node_id")
                    out(f"room_func: Callable = {room_name}")
                    out("recurse_depth += 1")
                    out("if recurse_depth > 1000:")
                    indent_inc()
                    out("raise RecursionError()")
                    indent_dec()
                    self.once_counter += 1
                    out(f"if {self.once_counter} not in _once:")
                    indent_inc()
                    out(f"_once.add({self.once_counter})")
                    out(f"random.seed({self.next_random_seed})")
                    out(f"state['{room_name}']['random_state'] = random.getstate()")
                    indent_dec()
                    out(f"random.setstate(state['{room_name}']['random_state'])")
                    out("option_list: list[tuple[str, Callable]] = list()")
                    out("while True:")
                    indent_inc()
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
        if _.strip():
            out(_)

    def labeled_statement(self, tree: Tree):
        _ = ""
        out("# labeled statement")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)

    def compound_statement(self, tree: Tree):
        out("# compound statement")
        out("while True:")
        indent_inc()
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)
        out("break  # end compound statement")
        indent_dec()

    def block_item_list(self, tree: Tree):
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)

    def block_item(self, tree: Tree):
        _ = ""
        out("# block_item")
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
            out(f"segment: any = {_.rstrip()}")
            out("if isinstance(segment, gamebook_core.AbstractItem):")
            indent_inc()
            out("state[room_name]['vars']['items'].add(segment)")
            indent_dec()
            out("elif isinstance(segment, gamebook_core.AbstractCharacter):")
            indent_inc()
            out("state[room_name]['vars']['items'].add(segment)")
            indent_dec()
            out("elif segment is not None:")
            indent_inc()
            out(f"out += \"\\n\\n\"")
            out(f"_ = html.escape(str(segment))")
            out(f"out += textwrap.dedent(_)")
            indent_dec()

    def selection_statement(self, tree: Tree):
        _ = ""
        out("# selection")
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
        out("# for each")
        postfix: Tree
        expression: Tree
        compound_statement: Tree
        _, postfix, expression, compound_statement = tree.children

        lvalue: str = self.visit(postfix)
        if lvalue == "state['world']":
            raise SyntaxError(f"Can not set world to a value. Only world members may be set.")
        saved_locals = self.scope_local.copy()
        if lvalue.startswith("state['world']['"):
            var = lvalue[len("state['world']['"):-2]
            if var not in self.scope_world and var not in self.scope_room:
                self.scope_local.add(var)
                out(f"# foreach local var: {var}")
            else:
                out(f"# foreach global or room var: {var}")

        out(f"# local vars: {self.scope_local}")
        out(f"for {self.visit(postfix)} in {self.visit(expression)}:")
        indent_inc()
        self.visit(compound_statement)
        indent_dec()
        self.scope_local.intersection_update(saved_locals)

    def repeat_statement(self, tree: Tree):
        out(f"# repeat statement {self.__top_level_children(tree)}")
        _, expression, statement = tree.children

        e = self.visit(expression)
        out(f"for _ in range({e}):")
        indent_inc()
        self.visit(statement)
        indent_dec()

    def jump_statement(self, tree: Tree):
        out("# jump")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)

    def goto_statement(self, tree: Tree):
        _, new_room, direction_facing, _ = tree.children
        func = self.next_goto
        out()
        out(f"def {func}():")
        indent_inc()
        out("global room_function_lookup")
        out("nonlocal _state")
        room: str = ""
        for _ in self.visit(new_room):
            room += _
        out(f"lookup: str = str({room})")
        out(f"if lookup not in room_function_lookup:")
        indent_inc()
        out(f"raise KeyError(f\"room {{lookup}} not found.\")")
        indent_dec()

        out(f"goto_saved_state = save_state()")

        facing = ""
        for _ in self.visit_children(direction_facing):
            facing += _
        if facing:
            out(f"state['world']['facing'].face({facing})")

        out(f"goto_destination_node: str = room_function_lookup[lookup]()")
        out(f"restore_state(goto_saved_state)")
        out(f"random.setstate(_state['random_state'])")
        out(f"return goto_destination_node")
        indent_dec()
        out(f"has_go_func = True")
        out(f"append_node: str = {func}()")
        out("_output_post_append[node_id] = append_node")
        out("break  # end processing after goto")
        return None

    def comment(self, tree: Tree):
        out("# comment")
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
        out(f"dir_saved_state = save_state()")
        if facing:
            out(f"state['world']['facing'].face({facing})")
        out(f"direction_destination: str = {room_func}() + \".md\"")
        out(f"restore_state(dir_saved_state)")
        out(f"random.setstate(_state['random_state'])")
        out(f"return direction_destination")
        indent_dec()
        out(f"option_list.append(({option_description}, {func}))")

    def option_statement(self, tree: Tree):
        _ = ""
        block: Tree = tree.children[1]
        option_description = self.visit(tree.children[0])  # basic_unescape(tree.children[0][1:-1])
        func: str = self.next_option
        out()
        saved_locals = self.scope_local.copy()
        closures: str = ""
        if self.scope_local:
            for var in self.scope_local:
                if closures:
                    closures += ", "
                # closures += f"_local_{var}=_ref_local_{var}"
                closures += f"_local_{var}=_local_{var}"
        out(f"def {func}({closures}) -> str:")
        indent_inc()
        out(f"\"\"\"{basic_escape(option_description)}\"\"\"")
        # out()
        out("global node_id_by_hash")
        out("global _output")
        out("nonlocal _state")
        out("nonlocal room_func")
        out()
        out("has_go_func: bool = False")
        out("# new node id may be needed")
        out(f"node_id: str = new_label('{func}')")
        out(f"option_saved_state = save_state()")
        out("out = ''")
        self.visit(block)
        out(f"node_hash: str = '{func}' + state_checksum()")
        # out("if node_hash in node_id_by_hash:")
        # indent_inc()
        # out("return node_id_by_hash[node_hash]")
        # indent_dec()
        out(f"if not has_go_func:")
        indent_inc()
        out(f"append_node: str = room_func()")
        out("_output_post_append[node_id] = append_node")
        out("node_id_by_hash[node_hash] = node_id")
        indent_dec()
        out(f"restore_state(option_saved_state)")
        out(f"random.setstate(_state['random_state'])")
        out("_output[node_id] = out")
        out("return node_id")
        indent_dec()
        out(f"option_list.append(({option_description}, {func}))")
        self.scope_local.intersection_update(saved_locals)
        out(f"# restored locals: {self.scope_local} was {saved_locals}")

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

    def python_list(self, tree: Tree):
        out(f"# python list {self.__top_level_children(tree)}")
        _ = "list("
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        _ += ")"
        return _

    def python_tuple(self, tree: Tree):
        out(f"# python tuple {self.__top_level_children(tree)}")
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
            var = lvalue[len("state['world']['"):-2]
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
        _ = "int(dice.roll("
        _ += f"str({self.visit(tree_count)})"
        _ += " + \"d\" + "
        _ += f"str({self.visit(tree_die)})"
        if self.visit(tree_explode):
            _ += " + \"x\""
        _ += "))"
        return _
    
    # max_dice_roll: "max" unary_expression "@" unary_expression dice_explode
    def max_dice_roll(self, tree: Tree) -> str:
        tree_count, tree_die, tree_explode = tree.children
        _ = "int(dice.roll_max("
        _ += f"str({self.visit(tree_count)})"
        _ += " + \"d\" + "
        _ += f"str({self.visit(tree_die)})"
        # if self.visit(tree_explode):
        #     _ += " + \"x\""
        _ += "))"
        return _

    # min_dice_roll: "min" unary_expression "@" unary_expression dice_explode
    def min_dice_roll(self, tree: Tree) -> str:
        tree_count, tree_die, tree_explode = tree.children
        _ = "int(dice.roll_min("
        _ += f"str({self.visit(tree_count)})"
        _ += " + \"d\" + "
        _ += f"str({self.visit(tree_die)})"
        # if self.visit(tree_explode):
        #     _ += " + \"x\""
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
        if scope == "room":
            self.scope_room.add(var)
        if scope == "local":
            self.scope_local.add(var)
            out(f"_local_{var}: any = None")

    def __default__(self, tree: Tree | Token):
        out(f"# __default__: {tree.data}")
        _ = ""
        for visit in self.visit_children(tree):
            if visit:
                _ += visit
        if _.strip():
            out(_)
