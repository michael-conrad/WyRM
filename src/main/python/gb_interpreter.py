import lark.visitors
from lark import Token
from lark import Tree


def unescape(cls, text: str) -> str:
    return text.encode('utf-8').decode('unicode-escape')


def escape(cls, text: str) -> str:
    return text.encode('unicode-escape').decode('utf-8')


class GamebookInterpreter(lark.visitors.Interpreter):

    globals: dict = dict()
    section_state: dict[str, dict[str, any]] = dict()
    section_stack: list[str] = list()

    def __init__(self):
        self.section_stack.append("book")
        self.section_state[self.current_section] = dict()

    @property
    def current_section(self) -> str:
        return self.section_stack[-1]

    def start(self, tree: Tree):
        self.visit_children(tree)

    def section(self, tree: Tree):
        self.visit_children(tree)
        self.section_stack.pop()

    def section_name(self, tree: Tree):
        for child in tree.children:
            if isinstance(child, Tree):
                self.visit(child)
            elif isinstance(child, Token):
                self.section_stack.append(child.value)
                if self.current_section not in self.section_state:
                    self.section_state[self.current_section] = dict()
                print(f"=== {child.value}")

    def metadata_namevalue(self, tree: Tree):
        child: Token | Tree

        tag: str = ""
        value: str = ""
        state: dict[str, any] = self.section_state[self.current_section]
        if "metadata" not in state:
            state["metadata"] = dict()
        metadata: dict[str, list[str]] = state["metadata"]

        for child in tree.children:
            if isinstance(child, Tree):
                self.visit(child)
            elif isinstance(child, Token):
                if child.type == "NAME":
                    tag = child.value.strip()
                elif child.type == "REMAINING_LINE":
                    value = child.value.strip()

        if tag not in metadata:
            metadata[tag] = list()
        metadata[tag].append(value)
        if tag.lower() == "library":
            value = value.strip()
            exec(f"import {value}", self.globals)


