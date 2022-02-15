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
    _state: str = "{}"
    path: list[str] = field(default_factory=list)
    rooms: str | None = None

    @property
    def state(self) -> dict[str, any] | None:
        if self._state is None:
            return None
        return jsonpickle.decode(self._state)

    @state.setter
    def state(self, state: dict[str, any]) -> None:
        self._state = jsonpickle.encode(state, keys=True)

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
        need_choices = "" if self.choices else "- TODO: CHOICES "
        section_marker: str = f"[{self.name}|{self.label}]{parents}" \
                              f" - End Game: {self.has_end_game}" \
                              f" {need_choices}"
        if len(section_marker) < 120:
            section_marker += ("=" * (120 - len(section_marker)))
        result: str = f"""
{section_marker}
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


def main() -> None:
    section_tag_match: str = "(?i)^\\[.*?|[a-z0-9]+]"
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
            if re.match(section_tag_match, line):
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
            if re.match("(?i)^\\[[a-z0-9_\\-|: .]+]", line.strip()):
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
                    new_section.text.append(f"")
                    new_section.text.append(f"!player.hit_points")
                    new_section.text.append(f"!player.weapon")
                    new_section.text.append(f"!player.armor_worn[0]")
                    new_section.text.append(f"!player.equipment_list")
                    new_section.text.append(f"!list_items(locals())")
                    new_section.text.append(f"!list_chars(locals())")
                    new_section.text.append(f"@turn: turn + 1")
                    new_section.text.append(f"@'' if turn % 20 != 0 else 'Torch starts guttering'")
                    new_section.text.append(f"")
                    new_section.text.append(f"@wander()")
                    new_section.text.append(f"")
                    new_section.text.append(f"!str([location, facing])")
                    new_section.text.append(f"; @facing: \"\"")
                    new_section.text.append(f"; @location: \"\"")
                    new_section.text.append(f"!room=rooms(location)")
                    new_section.text.append(f"!room")
                    new_section.text.append(f"")
    sections.extend(new_sections)
    print(f"Sections added: {len(new_sections):,}")
    new_sections.clear()

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
            if not section.parents:
                break
            have_parent: bool = False
            for parent in section.parents:
                if parent in sections_have:
                    have_parent = True
                    break
            if not have_parent:
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
            child_labels = get_child_section_labels(sections_lookup[_.label], sections_lookup, found_sections.copy())
            found_sections = found_sections.union(child_labels)
        return found_sections

    for section in sections:
        if end_game_label in get_child_section_labels(section, sections_by_label):
            section.has_end_game = True

    for section in sections:
        if not section.has_end_game:
            print(f"Section [{section.name}|{section.label}] has no end game.")

    for section in sections[1:]:
        section.state = None

    # Handle processing instructions such as roll dice
    for section in sections:
        state = section.state
        for lib in meta_header.libs:
            exec(f"from {lib} import *", state)
        if section.rooms:
            exec(f"restore_rooms({section.rooms})", state)
        # make sure certain variables are always available
        exec("locations=list() if 'locations' not in locals() else locations", state)
        exec("location='start' if 'location' not in locals() else location", state)
        exec("if not locations or locations[-1] != location: locations.append(location)", state)
        exec("turn=1 if 'turn' not in locals() else turn", state)
        exec("facing='?' if 'facing' not in locals() else facing", state)
        exec("room=rooms(location)", state)

        # start processing
        print()
        print(f"{section.name}|{section.label}")
        text_list = section.text.copy()
        section.text.clear()
        if section.path:
            for path in section.path:
                section.text.append(f";## -> {path}")
        section.text.append(f";## -> {section.name}|{section.label}")
        section.text.append(f"")
        location: str = eval("location", state)
        section.text.append(f";## Location: {location}")
        facing: str = eval("facing", state)
        section.text.append(f";## Facing: {facing}")
        locations: set[str] = eval("locations", state)
        if locations:
            section.text.append(f";## VISITED: {locations}")
        section.text.append(f"")
        section.text.append(";## DLs: Easy = 5, Routine = 7, Challenging = 9, Hard = 11, Extreme = 13")
        section.text.append(f"")
        if 'player' in state:
            needs_healing = eval("player.hp < player.hit_points_max // 2", state)
            if needs_healing:
                section.text.append(f";## ---> PLAYER NEEDS HEALING <---")
                section.text.append(f"")

        for line in text_list:
            line = line.strip()
            if line.startswith(";##"):
                continue
            print(f"{len(section.text) + 1:06} {line}")
            if line.startswith("!"):
                cmd: str = line[line.find("!") + 1:].strip()
                result: any = None
                try:
                    result = eval(cmd, state)
                except SyntaxError:
                    try:
                        result = exec(cmd, state)
                    except RuntimeError as e:
                        print(f"{e}")
                        print(f"{line}")
                if result is not None and isinstance(result, list):
                    line = ";;; " + line
                    section.text.append(line)
                    line = ""
                    for new_line in result:
                        section.text.append(str(new_line))
                elif result is not None:
                    if "#" in line:
                        line = line[:line.rfind('#')].strip()
                    line = f"{line} # {result}"
                section.text.append(line)
            elif line.startswith("@"):
                # saved eval
                cmd: str = line[line.find("@") + 1:]
                if ":" in line:
                    var: str = cmd[:cmd.find(":")].strip()
                    cmd = cmd[cmd.find(":") + 1:].lstrip()
                    result: any = eval(cmd, state)
                    if isinstance(result, list):
                        line = ";;; " + line
                        section.text.append(line)
                        line = ""
                        for new_line in result:
                            section.text.append(str(new_line))
                    elif isinstance(result, int):
                        line = f"!{var}= {result} # {line}"
                    elif isinstance(result, str):
                        line = f"!{var}= \"{result}\" # {line}"
                    else:
                        result = jsonpickle.encode(result, keys=True)
                        result = result.replace("\\", "\\\\")
                        result = result.replace("'", "\\'")
                        result = result.replace("\"", "\\\"")
                        line = f"!{var}= unpickle(\"{result}\") # {line}"
                    try:
                        exec(line[1:], state)
                    except NameError as e:
                        print(line)
                        raise e
                    section.text.append(line)
                else:
                    result: any = eval(cmd, state)
                    if isinstance(result, str):
                        result = "\"" + result.replace("\"", "\\\"") + "\""
                    line = f"; {result} # {line}"
                    section.text.append(line)
            else:
                section.text.append(line)

        section.state = state

        # determine child sections and clone environment into children
        for choice in section.choices:
            state: dict[str, any] = section.state
            child_section = sections_by_label[choice.label]
            child_section.rooms = eval(f"save_rooms()", state)
            child_section.path = section.path.copy()
            child_section.path.append(f"{section.name}|{section.label}")
            child_section.state = state

    with open(gb_file, "w") as w:
        w.write(str(meta_header))
        sections_have.clear()
        for section in sections:
            if ":" in section.name:
                continue
            if section.label in sections_have:
                continue
            sections_have.append(section.label)
            w.write(str(section))
        for section in sections:
            if ":" not in section.name:
                continue
            if section.label in sections_have:
                continue
            sections_have.append(section.label)
            w.write(str(
                section))  # subprocess.run(["git", "commit", "-m", "autosave [after]", gb_file],  #  #               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
