#!/usr/bin/env bash
"""true" '''\'
set -e
eval "$(conda shell.bash hook)"
conda deactivate
conda activate WyRM
exec python "$0" "$@"
exit $?
''"""
import argparse
import os.path
import random
import re
from dataclasses import dataclass
from dataclasses import field

import jsonpickle


def gamebook_file() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument('gamebook_file', type=str, help="GameBook File")
    return parser.parse_args().gamebook_file


@dataclass(slots=True)
class Choice:
    text: str = ""
    label: str = ""

    def __str__(self) -> str:
        return f":{self.text.strip()}|{self.label.strip()}"


@dataclass(slots=True)
class Section:
    name: str = ""
    label: str = ""
    parents: list[str] = field(default_factory=list)
    text: list[str] = field(default_factory=list)
    choices: list[Choice] = field(default_factory=list)
    has_end_game: bool = False

    def choice_labels(self) -> list[str]:
        choices: list[str] = list()
        for choice in self.choices:
            if not choice.label:
                continue
            choices.append(choice.label)
        return choices

    def needs_choice_labels(self) -> bool:
        for choice in self.choices:
            if not choice.label:
                return True
        return False

    def __str__(self) -> str:
        parents: str = ""
        for parent in self.parents:
            parents += f"{parent}; "
        if parents:
            parents = f" ({parents[:-2]})"
        else:
            parents = f" !!! (ORPHANED)"
        choices: str = ""
        for choice in self.choices:
            choices += f":{choice.text}|{choice.label}\n"
        text: str = ""
        prev_line: str = ""
        for line in self.text:
            if not prev_line and not line:
                continue
            text += f"{line}\n"
            prev_line = line
        result: str = f"""[{self.name}|{self.label}]{parents}
{text}
{choices}
"""
        return re.sub("\n\n+", "\n\n", result)


@dataclass(slots=True)
class Header:
    title: str = ""
    subtitle: str = ""
    author: str = ""
    license: str = ""

    notes: list[str] = field(default_factory=list)
    libs: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        notes: str = ""
        for note in self.notes:
            notes += f"Note: {note}\n"
        libs: str = ""
        for lib in self.libs:
            libs += f"Library: {lib}\n"
        result: str = f"""Title: {self.title}
Subtitle: {self.subtitle}
Author: {self.author}
License: {self.license}

{notes}
{libs}
"""
        return re.sub("\n\n+", "\n\n", result)


def new_label(already: set[str]) -> str:
    label: str = f"{random.randint(0, 4294967296 - 1):08x}"
    if label not in already:
        already.add(label)
    return label


def fstr(template, global_state: dict, local_state: dict):
    bs = ord("\\")
    template.replace("\\", f"{{chr({bs})}}")
    return eval(f"f'{template}'", global_state, local_state)


def main() -> None:
    gb_file: str = gamebook_file()
    if not os.path.exists(gb_file):
        raise RuntimeError(f"Unable to find '{gb_file}'")

    sections: list[Section] = list()
    section_labels: set[str] = set()
    meta_header: Header = Header()
    # Read in META
    with open(gb_file, "r") as f:
        for line in f:
            line = line.strip()
            if re.match("(?i)^\\[[a-z0-9_\\-|: ]+]", line):
                break
            if line.startswith("Title:"):
                meta_header.title = line[line.find(":") + 1:].strip()
                continue
            if line.startswith("Subtitle:"):
                meta_header.subtitle = line[line.find(":") + 1:].strip()
                continue
            if line.startswith("Author:"):
                meta_header.author = line[line.find(":") + 1:].strip()
                continue
            if line.startswith("Note:"):
                meta_header.notes.append(line[line.find(":") + 1:].strip())
                continue
            if line.startswith("License:"):
                meta_header.license = line[line.find(":") + 1:].strip()
                continue
            if line.startswith("Library:"):
                meta_header.libs.append(line[line.find(":") + 1:].strip())
                continue
            if not line.strip():
                continue
            raise RuntimeError(f"Unknown Metadata Tag: {line}")
    with open(gb_file, "r") as f:
        section: Section | None = None
        prev_line: str = ""
        for line in f:
            line = line.rstrip()
            if not prev_line and not line:
                continue
            prev_line = line
            # Parse Section Tag
            if re.match("(?i)^\\[[a-z0-9_\\-|: ]+]", line.strip()):
                section = Section()
                sections.append(section)
                data: str = line[line.find("[") + 1:line.rfind("]")]
                if "|" in data:
                    section.name = data[:data.find("|")].strip()
                    section.label = data[data.find("|") + 1:].strip()
                else:
                    section.name = data
                    section.label = ""
                continue
            if not section:
                continue
            # Parse Choices
            if line.lstrip().startswith(":"):
                data: str = line[line.find(":") + 1:]
                choice: Choice = Choice()
                section.choices.append(choice)
                if "|" in data:
                    choice.text = data[:data.find("|")].strip()
                    choice.label = data[data.find("|") + 1:].strip()
                else:
                    choice.text = data
                    choice.label = ""
                continue
            section.text.append(f"{line}")

    print(f"Found {len(sections):,} sections.")
    known_labels: set[str] = set()
    for section in sections:
        if section.label:
            known_labels.add(section.label)
    new_sections: list[Section] = list()

    for section in sections:
        if not section.label:
            section.label = new_label(known_labels)
        section_labels.add(section.label)

    for section in sections:
        if section.needs_choice_labels():
            choice: Choice
            for choice in section.choices:
                if not choice.label:
                    choice.label = new_label(known_labels)

    for section in sections:
        if section.choices:
            for choice in section.choices:
                if choice.label not in section_labels:
                    known_labels.add(choice.label)
                    new_section: Section = Section()
                    new_sections.append(new_section)
                    new_section.label = choice.label
                    new_section.name = choice.text
                    new_section.text.append(f"; {section.name}|{section.label}")
                    # new_section.parents.append(f"{section.label}")
    sections.extend(new_sections)
    new_sections.clear()
    print(f"Sections added: {len(new_sections):,}")

    for section in sections:
        if not section.choices and ":" not in section.name:
            print(f"Section [{section.name}|{section.label}] has no choices.")

    # Populate parent sections
    sections_dict: dict[str, Section] = dict()
    first_section: Section = sections[0]
    first_label: str = first_section.label
    for section in sections:
        sections_dict[section.label] = section
    for section in sections:
        for choice in section.choices:
            if choice.label == first_label:
                continue
            sections_dict[choice.label].parents.append(section.label)

    # Reorder sections to ensure parent environments are created first
    old_list = sections.copy()
    old_list.remove(first_section)

    sections.clear()
    sections.append(first_section)  # always keep first parent section first

    sections_have: list[str] = list()
    sections_have.append(first_section.label)

    while len(old_list):
        for section in old_list:
            if section in sections:
                break
            if section.parents and section.parents[0] not in sections_have:
                continue
            break
        old_list.remove(section)
        sections.append(section)
        sections_have.append(section.label)

    # Scan for branches that don't have an end game scenario
    sections_by_label: dict[str, Section] = dict()
    for section in sections:
        sections_by_label[section.label] = section
    end_game_label: str = sections[0].label

    def get_child_section_labels(starting_section: Section,  #
                                 sections_lookup: dict[str, Section],  #
                                 found_sections: set[str] = None) -> set[str]:
        if not found_sections:
            found_sections = set()
        for _ in starting_section.choices:
            if _.label in found_sections:
                continue
            found_sections.add(_.label)
            child_labels = get_child_section_labels(sections_lookup[_.label],
                                                    sections_lookup,
                                                    found_sections.copy())
            found_sections = found_sections.union(child_labels)
        return found_sections

    for section in sections:
        if end_game_label in get_child_section_labels():
            section.has_end_game = True

    # Handle processing instructions such as roll dice
    state: dict[str, dict] = dict()
    state[first_label] = dict()

    # Do the imports (Libraries)
    start_global: dict = dict()
    start_local: dict = dict()
    state[f"{first_section.label}_global"] = start_global
    state[f"{first_section.label}_local"] = start_local
    for lib in meta_header.libs:
        exec(f"from {lib} import *", start_global, start_local)

    for section in sections:
        # determine parent section and clone its environment into new section
        label_global: str = f"{section.label}_global"
        label_local: str = f"{section.label}_local"

        parent_global: str | None = None
        parent_local: str | None = None
        if section.parents:
            parent_global: str = f"{section.parents[0]}_global"
            parent_local: str = f"{section.parents[0]}_local"

        if parent_global and parent_global in state:
            state[label_global] = jsonpickle.decode(jsonpickle.encode(state[parent_global]))
        else:
            state[label_global] = start_global

        if parent_local and parent_local in state:
            state[label_local] = jsonpickle.decode(jsonpickle.encode(state[parent_local]))
        else:
            state[label_local] = start_local

        state_global: dict = start_global  # state[label_global]
        state_local: dict = state[label_local]

        for _, line in enumerate(section.text):
            line = line.strip()
            if line.startswith("!save_state"):
                continue
            if line.startswith("!"):
                cmd: str = line[line.find("!")+1:].strip()
                result: any = None
                try:
                    result = eval(cmd, state_global, state_local)
                except SyntaxError:
                    try:
                        result = exec(cmd, state_global, state_local)
                    except RuntimeError as e:
                        print(f"{e}")
                        print(f"{line}")
                if result:
                    if "#" in line:
                        line = line[:line.rfind('#')].strip()
                    line = f"{line} # {result}"
                section.text[_] = line

            elif line.startswith("@"):
                # saved eval
                cmd: str = line[line.find("@") + 1:]
                if ":" in line:
                    var: str = cmd[:cmd.find(":")].strip()
                    cmd = cmd[cmd.find(":")+1:].lstrip()
                    result: any = eval(cmd, state_global, state_local)
                    if isinstance(result, int):
                        section.text[_] = f"!{var}= {result} # {line}"
                    elif isinstance(result, str):
                        section.text[_] = f"!{var}= \"{result}\" # {line}"
                    else:
                        result = jsonpickle.encode(result, keys=True)
                        result = result.replace("\\", "\\\\")
                        result = result.replace("'", "\\'")
                        result = result.replace("\"", "\\\"")
                        section.text[_] = f"!{var}= unpickle(\"{result}\") # {line}"
                    try:
                        exec(section.text[_][1:], state_global, state_local)
                    except NameError as e:
                        print(section.text[_])
                        raise e
                else:
                    result: any = eval(cmd, state_global, state_local)
                    if isinstance(result, str):
                        result = "\"" + result.replace("\"", "\\\"") + "\""
                    section.text[_] = f"; {result} # {line}"
            else:
                section.text[_] = fstr(section.text[_].replace("'", "\\'"), state_global, state_local)

    with open(gb_file, "w") as w:
        w.write(str(meta_header))
        for section in sections:
            if ":" in section.name:
                continue
            w.write(str(section))
        for section in sections:
            if ":" not in section.name:
                continue
            w.write(str(section))
    #  subprocess.run(["git", "commit", "-m", "autosave [after]", gb_file],  #
    #               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
