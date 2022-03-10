import lark.visitors
from lark import Token
from lark import Tree


def unescape(text: str) -> str:
    return text.encode('utf-8').decode('unicode-escape')


def escape(text: str) -> str:
    return text.encode('unicode-escape').decode('utf-8')


class GamebookInterpreter(lark.visitors.Interpreter):
    """
    Two main phases:
     phase one (at init), store parsed tree
     phase two (on run), process stored and parsed tree as instructions
    """

    globals: dict = dict()
    section_state: dict[str, dict[str, any]] = dict()
    section_stack: list[str] = list()
    section_commands: dict[str, list[str]] = dict()

    def __init__(self):
        self.section_stack.append("Game Book")
        self.section_state[self.current_section] = dict()

    @property
    def current_section(self) -> str:
        return self.section_stack[-1]

    def start(self, tree: Tree):
        self.visit_children(tree)

    def section(self, tree: Tree):
        return self.visit_children(tree)

    def section_header(self, tree: Tree):
        return self.visit_children(tree)

    def section_name(self, tree: Tree):
        for child in tree.children:
            if isinstance(child, Token):
                if child.value in self.section_state:
                    raise SyntaxError(f"Section {child.value} previously defined.")
                self.section_stack.append(child.value)
                self.section_state[self.current_section] = dict()
                return str(child.value)

    def metadata_namevalue(self, tree: Tree):
        child: Token | Tree

        tag: str = ""
        value: str = ""
        state: dict[str, any] = self.section_state[self.current_section]
        if "metadata" not in state:
            state["metadata"] = dict()
        metadata: dict[str, list[str]] = state["metadata"]

        for child in tree.children:
            if isinstance(child, Token):
                if child.type == "NAME":
                    tag = child.value.strip()
                elif child.type == "REMAINING_LINE":
                    value = child.value.strip()

        if not tag:
            print("Bad Metadata Entry")
            return None
        if tag not in metadata:
            metadata[tag] = list()
        metadata[tag].append(value)
        if tag.lower() == "library":
            value = value.strip()
            if not value:
                print("Bad Library Entry Skipped")
                return
            return f"import {value}"

