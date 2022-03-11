from types import SimpleNamespace

import jsonpickle

state: SimpleNamespace = SimpleNamespace()

state.world = dict()
recurse_depth: int = 0
setattr(state, 'section_1', dict())


def save_state() -> dict[str, str]:
    global recurse_depth
    global state
    states: dict[str, str] = dict()
    states['recurse_depth'] = jsonpickle.encode(recurse_depth)
    states['state'] = jsonpickle.encode(state)
    return states


def restore_state(states: dict[str, str]) -> None:
    global recurse_depth
    global state
    recurse_depth = jsonpickle.decode(states['recurse_depth'])
    state = jsonpickle.decode(states['state'])

    return


saved = save_state()
state.x = "y"
print(jsonpickle.encode(state, unpicklable=True))
restore_state(saved)
print(jsonpickle.encode(state, unpicklable=True))
