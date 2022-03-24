# START
from contextlib import contextmanager
import re
import gamebook_core
from gamebook_core import *
import shutil
import os
import html
import dice
import hashlib
import random
import jsonpickle
from collections.abc import Callable
import textwrap

class NestedBreakException(Exception):
    pass


@contextmanager
def nested_break():
    """
    Enable proper use of "goto" to terminate all remaining code in a room.
    See: https://stackoverflow.com/a/3171971/12407701
    """
    
    try:
        yield NestedBreakException()
    except NestedBreakException as e:
        pass

# Rooms
repeat_state_tracking: dict[str, str] = dict()
state: dict[str, any] = dict()
state['world'] = dict()
recurse_depth: int = 0
imports = dict()
exec('from gamebook_core import *', imports)
for attr in [*imports]:
    state['world'][attr] = imports[attr]
state['world']['facing'] = state['world']['Facing']().with_facing('n')
# build up list of keys not to pickle or checksum
ignore_pickle_keys: set[str] = set()
for attr in [*imports]:
    ignore_pickle_keys.add(attr)
ignore_pickle_keys.add('__builtins__')
# Intentionally not tracked in state
_node_id: dict[str, int] = dict()


def copy(o: any) -> any:
    return jsonpickle.decode(jsonpickle.encode(any, keys=True), keys=True)


def face(facing: str):
    global state
    state['world']['facing'].face(facing)


def new_label(room: str = 'no-room') -> str:
    global _node_id
    if room not in _node_id:
        _node_id[room]=0
    _node_id[room] += 1
    cnt: int = _node_id[room]
    return f"{room}-{cnt:03x}"


_output: dict[str, str] = dict()
_output_post_append: dict[str, str] = dict()
node_id_by_hash: dict[str, str] = dict()

state['world']['__builtins__'] = globals()['__builtins__']

state['room_1'] = dict()
state['room_1']['once'] = set()
state['room_1']['vars'] = dict()
state['room_1']['vars']['items'] = gamebook_core.Items()
state['room_1']['random_state'] = random.Random(1).getstate()


def room_1() -> str:
    """init"""
    global _output
    global state
    global recurse_depth
    
    _sub_func_counter: int = 0
    _state: dict[str, any] = state['room_1']
    _once: set[int] = _state['once']
    room: str = "init"
    room_name: str = "room_1"
    # see if this is a repeating state, if yes, just use original node id
    global node_id_by_hash
    node_hash: str = room_name + state_checksum()
    if node_hash in node_id_by_hash:
        return node_id_by_hash[node_hash]
    node_id: str = new_label(room_name)
    node_id_by_hash[node_hash] = node_id
    
    next_turn()
    
    if turn() % 100 == 0:
        print(f'Turn: {turn()}')
    
    out = ''
    room_func: Callable = room_1
    recurse_depth += 1
    if recurse_depth > 1000:
        raise RecursionError()
    random.setstate(state['room_1']['random_state'])
    option_list: list[tuple[str, Callable]] = list()
    with nested_break() as abort_processing:
        segment: any = "# Init"
        if isinstance(segment, gamebook_core.AbstractItem):
            state[room_name]['vars']['items'].add(segment)
        elif isinstance(segment, gamebook_core.AbstractCharacter):
            state[room_name]['vars']['items'].add(segment)
        elif segment is not None:
            out += "\n\n"
            _ = html.escape(str(segment))
            out += textwrap.dedent(_)
        
        
        def go_000001():
            global room_function_lookup
            global node_id_by_hash
            nonlocal _state
            nonlocal node_id
            nonlocal _sub_func_counter
            
            _sub_func_counter += 1
            node_hash: str = 'go_000001' + str(_sub_func_counter) + state_checksum()
            if node_hash in node_id_by_hash:
                return node_id_by_hash[node_hash]
            
            goto_saved_state = save_state()
            lookup: str = str("Start")
            if lookup not in room_function_lookup:
                raise KeyError(f"room {lookup} not found.")
            state['world']['facing'].face("n")
            append_node: str = room_function_lookup[lookup]()
            node_id_by_hash[node_hash] = append_node
            restore_state(goto_saved_state)
            random.setstate(_state['random_state'])
            return append_node
        append_node: str = go_000001()
        _output_post_append[node_id] = append_node
        raise abort_processing # end processing after goto
    recurse_depth -= 1
    out += state[room_name]['vars']['items'].inv
    out += "\n\n"
    option_list.sort(key=lambda x: x[0])
    saved_state = save_state()
    for _ in option_list:
        destination_node = _[1]()
        restore_state(saved_state)
        _option_text: str = str(_[0])
        _option_text = html.escape(_option_text)
        _md_link: str = "[" + _option_text + "](" + destination_node + ".md)"
        out += "* " + _md_link
        out += "\n"
    restore_turn()
    _output[node_id] = out
    return node_id


state['room_2'] = dict()
state['room_2']['once'] = set()
state['room_2']['vars'] = dict()
state['room_2']['vars']['items'] = gamebook_core.Items()
state['room_2']['random_state'] = random.Random(2).getstate()


def room_2() -> str:
    """Start"""
    global _output
    global state
    global recurse_depth
    
    _sub_func_counter: int = 0
    _state: dict[str, any] = state['room_2']
    _once: set[int] = _state['once']
    room: str = "Start"
    room_name: str = "room_2"
    # see if this is a repeating state, if yes, just use original node id
    global node_id_by_hash
    node_hash: str = room_name + state_checksum()
    if node_hash in node_id_by_hash:
        return node_id_by_hash[node_hash]
    node_id: str = new_label(room_name)
    node_id_by_hash[node_hash] = node_id
    
    next_turn()
    
    if turn() % 100 == 0:
        print(f'Turn: {turn()}')
    
    out = ''
    room_func: Callable = room_2
    recurse_depth += 1
    if recurse_depth > 1000:
        raise RecursionError()
    random.setstate(state['room_2']['random_state'])
    option_list: list[tuple[str, Callable]] = list()
    with nested_break() as abort_processing:
        # world facing
        segment: any = "## Start"
        if isinstance(segment, gamebook_core.AbstractItem):
            state[room_name]['vars']['items'].add(segment)
        elif isinstance(segment, gamebook_core.AbstractCharacter):
            state[room_name]['vars']['items'].add(segment)
        elif segment is not None:
            out += "\n\n"
            _ = html.escape(str(segment))
            out += textwrap.dedent(_)
        segment: any = "Facing: {facing.facing}".format(facing=state['world']['facing'])
        if isinstance(segment, gamebook_core.AbstractItem):
            state[room_name]['vars']['items'].add(segment)
        elif isinstance(segment, gamebook_core.AbstractCharacter):
            state[room_name]['vars']['items'].add(segment)
        elif segment is not None:
            out += "\n\n"
            _ = html.escape(str(segment))
            out += textwrap.dedent(_)
        
        def option_000002() -> str:
            """\"North\""""
            global node_id_by_hash
            global _output
            nonlocal _state
            nonlocal room_func
            nonlocal _sub_func_counter
            
            _sub_func_counter += 1
            node_hash: str = 'option_000002' + str(_sub_func_counter) + state_checksum()
            if node_hash in node_id_by_hash:
                return node_id_by_hash[node_hash]
            option_saved_state = save_state()
            
            node_id: str = new_label('option_000002')
            node_id_by_hash[node_hash] = node_id
            
            with nested_break() as abort_processing:
                out = ''
                # compound statement
                
                
                def go_000003():
                    global room_function_lookup
                    global node_id_by_hash
                    nonlocal _state
                    nonlocal node_id
                    nonlocal _sub_func_counter
                    
                    _sub_func_counter += 1
                    node_hash: str = 'go_000003' + str(_sub_func_counter) + state_checksum()
                    if node_hash in node_id_by_hash:
                        return node_id_by_hash[node_hash]
                    
                    goto_saved_state = save_state()
                    lookup: str = str("1")
                    if lookup not in room_function_lookup:
                        raise KeyError(f"room {lookup} not found.")
                    state['world']['facing'].face("n")
                    append_node: str = room_function_lookup[lookup]()
                    node_id_by_hash[node_hash] = append_node
                    restore_state(goto_saved_state)
                    random.setstate(_state['random_state'])
                    return append_node
                append_node: str = go_000003()
                _output_post_append[node_id] = append_node
                raise abort_processing # end processing after goto
                append_node: str = room_func()
                _output_post_append[node_id] = append_node
            restore_state(option_saved_state)
            random.setstate(_state['random_state'])
            _output[node_id] = out
            return node_id
        option_list.append(("North", option_000002))
        # restored locals: set() was set()
        
        def option_000004() -> str:
            """\"South\""""
            global node_id_by_hash
            global _output
            nonlocal _state
            nonlocal room_func
            nonlocal _sub_func_counter
            
            _sub_func_counter += 1
            node_hash: str = 'option_000004' + str(_sub_func_counter) + state_checksum()
            if node_hash in node_id_by_hash:
                return node_id_by_hash[node_hash]
            option_saved_state = save_state()
            
            node_id: str = new_label('option_000004')
            node_id_by_hash[node_hash] = node_id
            
            with nested_break() as abort_processing:
                out = ''
                # compound statement
                
                
                def go_000005():
                    global room_function_lookup
                    global node_id_by_hash
                    nonlocal _state
                    nonlocal node_id
                    nonlocal _sub_func_counter
                    
                    _sub_func_counter += 1
                    node_hash: str = 'go_000005' + str(_sub_func_counter) + state_checksum()
                    if node_hash in node_id_by_hash:
                        return node_id_by_hash[node_hash]
                    
                    goto_saved_state = save_state()
                    lookup: str = str("2")
                    if lookup not in room_function_lookup:
                        raise KeyError(f"room {lookup} not found.")
                    state['world']['facing'].face("s")
                    append_node: str = room_function_lookup[lookup]()
                    node_id_by_hash[node_hash] = append_node
                    restore_state(goto_saved_state)
                    random.setstate(_state['random_state'])
                    return append_node
                append_node: str = go_000005()
                _output_post_append[node_id] = append_node
                raise abort_processing # end processing after goto
                append_node: str = room_func()
                _output_post_append[node_id] = append_node
            restore_state(option_saved_state)
            random.setstate(_state['random_state'])
            _output[node_id] = out
            return node_id
        option_list.append(("South", option_000004))
        # restored locals: set() was set()
        # iteration
        # for statement
        _local_ix=0
        while True:
            _ = _local_ix<3
            if not _:
                break  # exit for loop
            # compound statement
            
            def option_000006(_local_ix=_local_ix) -> str:
                """\"North Message {ix}\".format(ix=_local_ix)"""
                global node_id_by_hash
                global _output
                nonlocal _state
                nonlocal room_func
                nonlocal _sub_func_counter
                
                _sub_func_counter += 1
                node_hash: str = 'option_000006' + str(_sub_func_counter) + state_checksum()
                if node_hash in node_id_by_hash:
                    return node_id_by_hash[node_hash]
                option_saved_state = save_state()
                
                node_id: str = new_label('option_000006')
                node_id_by_hash[node_hash] = node_id
                
                with nested_break() as abort_processing:
                    out = ''
                    # compound statement
                    segment: any = "North Message {ix}".format(ix=_local_ix)
                    if isinstance(segment, gamebook_core.AbstractItem):
                        state[room_name]['vars']['items'].add(segment)
                    elif isinstance(segment, gamebook_core.AbstractCharacter):
                        state[room_name]['vars']['items'].add(segment)
                    elif segment is not None:
                        out += "\n\n"
                        _ = html.escape(str(segment))
                        out += textwrap.dedent(_)
                    append_node: str = room_func()
                    _output_post_append[node_id] = append_node
                restore_state(option_saved_state)
                random.setstate(_state['random_state'])
                _output[node_id] = out
                return node_id
            option_list.append(("North Message {ix}".format(ix=_local_ix), option_000006))
            # restored locals: {'ix'} was {'ix'}
            
            def option_000007(_local_ix=_local_ix) -> str:
                """\"South Message {ix}\".format(ix=_local_ix)"""
                global node_id_by_hash
                global _output
                nonlocal _state
                nonlocal room_func
                nonlocal _sub_func_counter
                
                _sub_func_counter += 1
                node_hash: str = 'option_000007' + str(_sub_func_counter) + state_checksum()
                if node_hash in node_id_by_hash:
                    return node_id_by_hash[node_hash]
                option_saved_state = save_state()
                
                node_id: str = new_label('option_000007')
                node_id_by_hash[node_hash] = node_id
                
                with nested_break() as abort_processing:
                    out = ''
                    # compound statement
                    segment: any = "South Message {ix}".format(ix=_local_ix)
                    if isinstance(segment, gamebook_core.AbstractItem):
                        state[room_name]['vars']['items'].add(segment)
                    elif isinstance(segment, gamebook_core.AbstractCharacter):
                        state[room_name]['vars']['items'].add(segment)
                    elif segment is not None:
                        out += "\n\n"
                        _ = html.escape(str(segment))
                        out += textwrap.dedent(_)
                    append_node: str = room_func()
                    _output_post_append[node_id] = append_node
                restore_state(option_saved_state)
                random.setstate(_state['random_state'])
                _output[node_id] = out
                return node_id
            option_list.append(("South Message {ix}".format(ix=_local_ix), option_000007))
            # restored locals: {'ix'} was {'ix'}
            _local_ix+=1
    recurse_depth -= 1
    out += state[room_name]['vars']['items'].inv
    out += "\n\n"
    option_list.sort(key=lambda x: x[0])
    saved_state = save_state()
    for _ in option_list:
        destination_node = _[1]()
        restore_state(saved_state)
        _option_text: str = str(_[0])
        _option_text = html.escape(_option_text)
        _md_link: str = "[" + _option_text + "](" + destination_node + ".md)"
        out += "* " + _md_link
        out += "\n"
    restore_turn()
    _output[node_id] = out
    return node_id


state['room_3'] = dict()
state['room_3']['once'] = set()
state['room_3']['vars'] = dict()
state['room_3']['vars']['items'] = gamebook_core.Items()
state['room_3']['random_state'] = random.Random(3).getstate()


def room_3() -> str:
    """1"""
    global _output
    global state
    global recurse_depth
    
    _sub_func_counter: int = 0
    _state: dict[str, any] = state['room_3']
    _once: set[int] = _state['once']
    room: str = "1"
    room_name: str = "room_3"
    # see if this is a repeating state, if yes, just use original node id
    global node_id_by_hash
    node_hash: str = room_name + state_checksum()
    if node_hash in node_id_by_hash:
        return node_id_by_hash[node_hash]
    node_id: str = new_label(room_name)
    node_id_by_hash[node_hash] = node_id
    
    next_turn()
    
    if turn() % 100 == 0:
        print(f'Turn: {turn()}')
    
    out = ''
    room_func: Callable = room_3
    recurse_depth += 1
    if recurse_depth > 1000:
        raise RecursionError()
    random.setstate(state['room_3']['random_state'])
    option_list: list[tuple[str, Callable]] = list()
    with nested_break() as abort_processing:
        segment: any = "## 1"
        if isinstance(segment, gamebook_core.AbstractItem):
            state[room_name]['vars']['items'].add(segment)
        elif isinstance(segment, gamebook_core.AbstractCharacter):
            state[room_name]['vars']['items'].add(segment)
        elif segment is not None:
            out += "\n\n"
            _ = html.escape(str(segment))
            out += textwrap.dedent(_)
        segment: any = "Facing: {facing.facing}".format(facing=state['world']['facing'])
        if isinstance(segment, gamebook_core.AbstractItem):
            state[room_name]['vars']['items'].add(segment)
        elif isinstance(segment, gamebook_core.AbstractCharacter):
            state[room_name]['vars']['items'].add(segment)
        elif segment is not None:
            out += "\n\n"
            _ = html.escape(str(segment))
            out += textwrap.dedent(_)
        
        def option_000008() -> str:
            """\"South\""""
            global node_id_by_hash
            global _output
            nonlocal _state
            nonlocal room_func
            nonlocal _sub_func_counter
            
            _sub_func_counter += 1
            node_hash: str = 'option_000008' + str(_sub_func_counter) + state_checksum()
            if node_hash in node_id_by_hash:
                return node_id_by_hash[node_hash]
            option_saved_state = save_state()
            
            node_id: str = new_label('option_000008')
            node_id_by_hash[node_hash] = node_id
            
            with nested_break() as abort_processing:
                out = ''
                # compound statement
                
                
                def go_000009():
                    global room_function_lookup
                    global node_id_by_hash
                    nonlocal _state
                    nonlocal node_id
                    nonlocal _sub_func_counter
                    
                    _sub_func_counter += 1
                    node_hash: str = 'go_000009' + str(_sub_func_counter) + state_checksum()
                    if node_hash in node_id_by_hash:
                        return node_id_by_hash[node_hash]
                    
                    goto_saved_state = save_state()
                    lookup: str = str("Start")
                    if lookup not in room_function_lookup:
                        raise KeyError(f"room {lookup} not found.")
                    state['world']['facing'].face("s")
                    append_node: str = room_function_lookup[lookup]()
                    node_id_by_hash[node_hash] = append_node
                    restore_state(goto_saved_state)
                    random.setstate(_state['random_state'])
                    return append_node
                append_node: str = go_000009()
                _output_post_append[node_id] = append_node
                raise abort_processing # end processing after goto
                append_node: str = room_func()
                _output_post_append[node_id] = append_node
            restore_state(option_saved_state)
            random.setstate(_state['random_state'])
            _output[node_id] = out
            return node_id
        option_list.append(("South", option_000008))
        # restored locals: set() was set()
    recurse_depth -= 1
    out += state[room_name]['vars']['items'].inv
    out += "\n\n"
    option_list.sort(key=lambda x: x[0])
    saved_state = save_state()
    for _ in option_list:
        destination_node = _[1]()
        restore_state(saved_state)
        _option_text: str = str(_[0])
        _option_text = html.escape(_option_text)
        _md_link: str = "[" + _option_text + "](" + destination_node + ".md)"
        out += "* " + _md_link
        out += "\n"
    restore_turn()
    _output[node_id] = out
    return node_id


state['room_4'] = dict()
state['room_4']['once'] = set()
state['room_4']['vars'] = dict()
state['room_4']['vars']['items'] = gamebook_core.Items()
state['room_4']['random_state'] = random.Random(4).getstate()


def room_4() -> str:
    """2"""
    global _output
    global state
    global recurse_depth
    
    _sub_func_counter: int = 0
    _state: dict[str, any] = state['room_4']
    _once: set[int] = _state['once']
    room: str = "2"
    room_name: str = "room_4"
    # see if this is a repeating state, if yes, just use original node id
    global node_id_by_hash
    node_hash: str = room_name + state_checksum()
    if node_hash in node_id_by_hash:
        return node_id_by_hash[node_hash]
    node_id: str = new_label(room_name)
    node_id_by_hash[node_hash] = node_id
    
    next_turn()
    
    if turn() % 100 == 0:
        print(f'Turn: {turn()}')
    
    out = ''
    room_func: Callable = room_4
    recurse_depth += 1
    if recurse_depth > 1000:
        raise RecursionError()
    random.setstate(state['room_4']['random_state'])
    option_list: list[tuple[str, Callable]] = list()
    with nested_break() as abort_processing:
        segment: any = "## 2"
        if isinstance(segment, gamebook_core.AbstractItem):
            state[room_name]['vars']['items'].add(segment)
        elif isinstance(segment, gamebook_core.AbstractCharacter):
            state[room_name]['vars']['items'].add(segment)
        elif segment is not None:
            out += "\n\n"
            _ = html.escape(str(segment))
            out += textwrap.dedent(_)
        segment: any = "Facing: {facing.facing}".format(facing=state['world']['facing'])
        if isinstance(segment, gamebook_core.AbstractItem):
            state[room_name]['vars']['items'].add(segment)
        elif isinstance(segment, gamebook_core.AbstractCharacter):
            state[room_name]['vars']['items'].add(segment)
        elif segment is not None:
            out += "\n\n"
            _ = html.escape(str(segment))
            out += textwrap.dedent(_)
        
        def option_000010() -> str:
            """\"North\""""
            global node_id_by_hash
            global _output
            nonlocal _state
            nonlocal room_func
            nonlocal _sub_func_counter
            
            _sub_func_counter += 1
            node_hash: str = 'option_000010' + str(_sub_func_counter) + state_checksum()
            if node_hash in node_id_by_hash:
                return node_id_by_hash[node_hash]
            option_saved_state = save_state()
            
            node_id: str = new_label('option_000010')
            node_id_by_hash[node_hash] = node_id
            
            with nested_break() as abort_processing:
                out = ''
                # compound statement
                
                
                def go_000011():
                    global room_function_lookup
                    global node_id_by_hash
                    nonlocal _state
                    nonlocal node_id
                    nonlocal _sub_func_counter
                    
                    _sub_func_counter += 1
                    node_hash: str = 'go_000011' + str(_sub_func_counter) + state_checksum()
                    if node_hash in node_id_by_hash:
                        return node_id_by_hash[node_hash]
                    
                    goto_saved_state = save_state()
                    lookup: str = str("Start")
                    if lookup not in room_function_lookup:
                        raise KeyError(f"room {lookup} not found.")
                    state['world']['facing'].face("n")
                    append_node: str = room_function_lookup[lookup]()
                    node_id_by_hash[node_hash] = append_node
                    restore_state(goto_saved_state)
                    random.setstate(_state['random_state'])
                    return append_node
                append_node: str = go_000011()
                _output_post_append[node_id] = append_node
                raise abort_processing # end processing after goto
                append_node: str = room_func()
                _output_post_append[node_id] = append_node
            restore_state(option_saved_state)
            random.setstate(_state['random_state'])
            _output[node_id] = out
            return node_id
        option_list.append(("North", option_000010))
        # restored locals: set() was set()
    recurse_depth -= 1
    out += state[room_name]['vars']['items'].inv
    out += "\n\n"
    option_list.sort(key=lambda x: x[0])
    saved_state = save_state()
    for _ in option_list:
        destination_node = _[1]()
        restore_state(saved_state)
        _option_text: str = str(_[0])
        _option_text = html.escape(_option_text)
        _md_link: str = "[" + _option_text + "](" + destination_node + ".md)"
        out += "* " + _md_link
        out += "\n"
    restore_turn()
    _output[node_id] = out
    return node_id


room_function_lookup: dict[str, Callable] = dict()
room_function_lookup["init"] = room_1
room_function_lookup["Start"] = room_2
room_function_lookup["1"] = room_3
room_function_lookup["2"] = room_4


def state_checksum() -> str:
    pickled: str = save_state()
    node_hash: str = hashlib.sha512(pickled.encode('utf-8')).hexdigest()
    return node_hash


def save_state() -> str:
    saved_states: dict[str, dict | str] = dict()
    saved_states['world_vars']: dict[str, any] = dict()
    for var in state['world'].keys():
        if var in ignore_pickle_keys:
            continue
        saved_states['world_vars'][var] = state['world'][var]
    saved_states['room_1'] = state['room_1']
    saved_states['room_2'] = state['room_2']
    saved_states['room_3'] = state['room_3']
    saved_states['room_4'] = state['room_4']
    return jsonpickle.encode(saved_states, keys=True)


def restore_state(_saved_states: str) -> None:
    saved_states = jsonpickle.decode(_saved_states, keys=True)
    for var in saved_states['world_vars'].keys():
        state['world'][var] = saved_states['world_vars'][var]
    state['room_1'] = saved_states['room_1']
    state['room_2'] = saved_states['room_2']
    state['room_3'] = saved_states['room_3']
    state['room_4'] = saved_states['room_4']
    return


index_node: str = room_1()

import mdformat
md_options: dict[str, any] = dict()
md_options["wrap"] = 80

shutil.rmtree("md", ignore_errors=True)
os.makedirs("md", exist_ok=True)
for append_to in _output_post_append:
    append_from: str = _output_post_append[append_to]
    _output[append_to] += '\n\n' + _output[append_from]
for key in _output:
    out = mdformat.text(_output[key], options=md_options)
    with open("md/" + key + ".md", "w") as w:
        w.write("\n")
        w.write(out)
        w.write("\n")

with open("md/index.md", "w") as w:
    out = mdformat.text(_output[index_node], options=md_options)
    w.write("\n")
    w.write(out)
    w.write("\n")

