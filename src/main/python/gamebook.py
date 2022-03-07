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
import textwrap
import time
from dataclasses import dataclass
from dataclasses import field

import jsonpickle

from character_sheet import CharacterSheet


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
    _location: str = ""
    parents: list[str] = field(default_factory=list)
    text: list[str] = field(default_factory=list)
    choices: list[Choice] = field(default_factory=list)
    has_end_game: bool = False
    _state: str = "{}"
    path: list[str] = field(default_factory=list)
    rooms: str | None = None

    @property
    def location(self) -> str:
        return self._location

    @location.setter
    def location(self, location: str) -> None:
        self._location = location

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

    def html(self) -> str:
        parents: str = ""
        for parent in self.parents:
            parents += f"{parent}; "
        if parents:
            parents = f" ({parents[:-2]})"
        else:
            parents = f" !!! (ORPHANED)"
        choices: str = ""
        for choice in self.choices:
            choices += f":<a href='#{choice.label}'>{Section.escape_html(choice.text)}|{choice.label}</a><br/>\n"
        text: str = ""
        prev_line: str = ""
        ul_mode: bool = False
        div_started: bool = False
        for line in self.text:
            line = line.strip()
            if line.startswith(";") or line.startswith("!"):
                continue
            if not prev_line and not line:
                continue
            prev_line = line
            if not div_started:
                text += "\n<div style='margin-bottom: 1em;'>\n"
                div_started = True

            li_mode: bool = line.startswith("*")
            h_mode: int = 1 if line.startswith("#") else 0
            h_mode: int = 2 if line.startswith("##") else h_mode
            h_mode: int = 3 if line.startswith("###") else h_mode
            if h_mode:
                line = line[h_mode:]
                if div_started:
                    div_started = False
                    text += "\n</div>\n"

            line = Section.escape_html(line)
            if li_mode:
                line = f"<li>{line[1:]}</li>\n"
            if li_mode and not ul_mode:
                ul_mode = True
                line = f"\n<ul>\n{line}"
            elif not li_mode and ul_mode:
                ul_mode = False
                line = f"{line}\n</ul>\n"
            if h_mode:
                line = f"<h{h_mode}>{line}</h{h_mode}>\n"
            if line:
                text += f"{line}\n"
            else:
                if div_started:
                    text += "\n</div>\n"
                    div_started = False
        if div_started:
            text += "\n</div>\n"
        # text = re.sub("(.*)\n\n", "<div>\\1</div>\n", text)
        need_choices = "" if self.choices else "- TODO: CHOICES "
        section_marker: str = f"<hr/>" \
                              f"<a id='{Section.escape_html(self.label)}'></a>" \
                              f"[{Section.escape_html(self.name)}|{self.label}]{parents}" \
                              f" - End Game: {self.has_end_game}" \
                              f" {need_choices}"
        result: str = f"""<div style='margin-bottom: 400px;'>
    <pre>{section_marker}</pre>
    <div class='Section'>{text}</div>
    <div style='margin-top: 0.25 em; margin-left: 1em;'>{choices}</div>
    </div>"""
        return re.sub("\n\n+", "\n", result)

    @classmethod
    def escape_html(cls, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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

    def html(self) -> str:
        notes: str = ""
        for note in self.notes:
            notes += f"Note: {note}<br/>"
        libs: str = ""
        result: str = f"""<div class='Header'>
        Title: {self.title}<br/>
        Subtitle: {self.subtitle}<br/>
        Author: {self.author}<br/>
        License: {self.license}<br/>
        <hr/>
        {notes}
        </div>"""
        return re.sub("\n\n+", "\n", result)


def new_label(already: set[str]) -> str:
    label: str = f"{random.randint(0, 4294967296 - 1):08x}"
    if label not in already:
        already.add(label)
    return label


def main() -> None:
    random.seed(time.time())
    section_tag_match: str = "(?i)^\\[[^|]+\\|.*?]"
    gb_file: str = gamebook_file()
    html_file: str = os.path.splitext(gb_file)[0] + ".html"
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
    already: set[str] = set()
    with open(gb_file, "r") as f:
        section: Section | None = None
        prev_line: str = ""
        for line in f:
            line = line.rstrip()
            if not prev_line and not line:
                continue
            prev_line = line
            # Parse Section Tag
            if re.match(section_tag_match, line.strip()):
                section = Section()
                data: str = line[line.find("[") + 1:line.rfind("]")]
                if "|" in data:
                    section.name = data[:data.find("|")].strip()
                    section.label = data[data.find("|") + 1:].strip()
                else:
                    section.name = data
                    section.label = ""
                if section.label and section.label in already:
                    section = None
                    continue
                if section.name[-1] not in "!.?":
                    section.name += "."
                sections.append(section)
                already.add(section.label)
                continue
            if section is None:
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
                if choice.text[-1] not in "!.?":
                    choice.text += "."
                continue
            if line.lstrip().startswith("["):
                line = f"; {line}"
            section.text.append(f"{line}")

    # sort choices by description text
    for section in sections:
        if section.choices:
            section.choices.sort(key=lambda x: x.text.strip())

    # re-layout text sections for consistency
    for section in sections:
        new_text: list[str] = list()
        new_text.append("")
        for line in section.text:
            line = line.strip()
            if not line:
                if new_text[-1]:
                    new_text.append("")
                new_text.append("")
                continue
            if line.startswith("#") or line.startswith("*"):
                new_text.append(line)
                continue
            if line.startswith(";") or line.startswith("!") or line.startswith("@"):
                if new_text[-1]:
                    new_text.append(line)
                    new_text.append("")
                else:
                    new_text[-1] = line
                    new_text.append("")
                continue
            new_text[-1] = textwrap.fill(f"{new_text[-1]} {line}", 80)
        section.text.clear()
        section.text.extend(new_text)

    # scan for repeats
    for section in sections:
        new_text: list[str] = list()
        for line in section.text:
            if not line:
                new_text.append("")
                continue
            if re.match("^!\\d+ ", line):
                new_text.append(f";;; {line}")
                repeat: int = int(line[1:line.index(" ")])
                line = line[line.index(" ") + 1:]
                for _ in range(repeat):
                    new_text.append(f"!{line}")
                continue
            new_text.append(line)
        section.text.clear()
        section.text.extend(new_text)

    print(f"Found {len(sections):,} sections.")
    known_labels: set[str] = set()
    for section in sections:
        if section.label in known_labels:
            raise Exception(f"Duplicate Section Label: {section.label}")
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
            for _, choice in enumerate(section.choices):
                if choice.label not in section_labels:
                    known_labels.add(choice.label)
                    section_labels.add(choice.label)
                    new_section: Section = Section()
                    new_section.label = choice.label
                    new_section.name = choice.text
                    auto_go: str
                    if ":" in new_section.name:
                        section.choices[_].text=choice.text[:choice.text.index(":")]
                        auto_go = new_section.name[new_section.name.index(":")+1:].strip()
                        if auto_go[-1] in ".?!":
                            auto_go = auto_go[:-1]
                    else:
                        auto_go = ""
                    new_section.text.append(f"!NPC.set_section_tag(\"{section.label}\")")
                    new_section.text.append(f"")
                    new_section.text.append(f"@turn: turn + 1")
                    new_section.text.append(f"@''"
                                            f" if (player.darkvision or turn % 20 != 0)"
                                            f" else 'Torch starts sputtering'")
                    new_section.text.append(f"")
                    if auto_go:
                        new_section.text.append(f"!room.info_directions")
                        new_section.text.append(f"!room.go(\"{auto_go}\")")
                    else:
                        new_section.text.append(f"!room.info")
                        new_section.text.append(f";!room.go(\"\")")
                    new_section.text.append(f"")
                    new_section.text.append(f"@wander(6, 1) if turn < 10 else ''")
                    new_section.text.append(f"@wander(6, 2) if turn >= 10 and turn < 20 else ''")
                    new_section.text.append(f"@wander(6, 3) if turn >= 20 and turn < 30 else ''")
                    new_section.text.append(f"@wander(6, 4) if turn >= 30 else ''")
                    new_section.text.append(f"")

                    new_sections.append(new_section)
    print(f"Sections to add: {len(new_sections):,}")

    sections.extend(new_sections)
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
            sections_dict[choice.label].name=choice.text

    # Reorder sections to ensure parent environments are created first
    old_list: list[Section] = [old_section for old_section in sections_dict.values()]
    old_list.remove(first_section)
    old_list.sort(key=lambda x: x.label)

    sections.clear()
    sections.append(first_section)  # always keep first parent section first

    sections_have: set[str] = set()
    sections_have.add(first_section.label)

    while len(old_list):
        for section in old_list:
            if not section.parents:
                continue
            have_parent: bool = False
            for parent in section.parents:
                if parent in sections_have:
                    have_parent = True
                    break
            if have_parent:
                break
        sections_have.add(section.label)
        sections.append(section)
        old_list.remove(section)

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
            if _.label in sections_lookup:
                child_labels = get_child_section_labels(sections_lookup[_.label], sections_lookup,
                                                        found_sections.copy())
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
        # start processing
        print()
        print(f"{section.name}|{section.label}")

        state = section.state
        if state is None:
            continue
        text_list: list[str] = list()
        for line in section.text:
            if "\n" in line:
                for split in line.split("\n"):
                    text_list.append(split.strip())
            else:
                text_list.append(line)
        section.text.clear()

        for lib in meta_header.libs:
            exec(f"from {lib} import *", state)
        # always reset section tag to None at start of each section run
        exec("NPC.set_section_tag(None)", state)
        if section.rooms:
            exec(f"restore_rooms({section.rooms})", state)
        # make sure certain variables are always available
        if "locations" not in state:
            state["locations"] = list()
        if "location" not in state:
            state["location"] = "start"
        locations: list[str] = state["locations"]
        if not locations or locations[-1] != state["location"]:
            locations.append(state["location"])
        if "turn" not in state:
            state["turn"] = 1
        if "facing" not in state:
            state["facing"]="?"
        exec("room=rooms(location)", state)
        if "notes" not in state:
            state["notes"] = list()
        if "note" not in state:
            state["note"] = list()
        state["section"] = section.label
        # special for vitality potion drinking or other vitality item usage
        if "vitality" not in state:
            state["vitality"] = 0
        if "player" in state:
            player: CharacterSheet = state["player"]
            player.massive_attack = True
            vitality: int = state["vitality"]
            if vitality:
                if player.hp < player.hit_points_max:
                    player.hp += min(2, vitality)
                state["vitality"] = max(0, vitality-2)

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
        note: str = state["note"]
        if note:
            section.text.append(f";## Note: {note}")
        if state['vitality'] and state['player']:
            section.text.append(f";## Vitality remaining: {state['vitality']}")
            section.text.append(f";## Player HP: {state['player'].hp}")
        section.text.append(";## DLs: Easy = 5, Routine = 7, Challenging = 9, Hard = 11, Extreme = 13")
        section.text.append(f"")
        section.text.append(eval("rooms_status()", state))
        for line in text_list:
            line = line.strip()
            if line.startswith(";##"):
                continue
            print(f"{len(section.text) + 1:06} {line}")
            if line.startswith("!"):
                cmd: str = line[1:].strip()
                result: any = None
                try:
                    result = eval(cmd, state)
                except SyntaxError:
                    try:
                        result = exec(cmd, state)
                    except Exception as e:
                        raise e
                if result is not None and isinstance(result, list):
                    line = ";;; " + line
                    section.text.append(line)
                    line = ""
                    for new_line in result:
                        section.text.append(str(new_line))
                elif result is not None:
                    line = line.strip()
                    if "#" in line and "\"" not in line and "'" not in line:
                        line = line[:line.index("#")].strip()
                        line = f"{line} # {result}"
                    elif "#" in line:
                        line = f"{line}\n;## {result}"
                    else:
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
                        pickled = jsonpickle.encode(result, use_base85=True, indent=None) \
                            .replace("\\", "\\\\") \
                            .replace("'", "\'")
                        line = f"!{var}= unpickle('{pickled}') # {line}"
                        section.text.append(line)
                        section.text.append(f";;; !{var}")
                        for l in result:
                            section.text.append(l)
                        line = ""
                    elif isinstance(result, int):
                        line = f"!{var}= {result} # {line}"
                    elif isinstance(result, str):
                        result = result.replace("\"", "\\\"")
                        line = f"!{var}= \"{result}\" # {line}"
                    else:
                        result = jsonpickle.encode(result, use_base85=True, indent=None) \
                            .replace("\\", "\\\\") \
                            .replace("'", "\\'")
                        result = f"'{result}'"
                        line = f"!{var}= unpickle({result}) # {line}"
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
                if re.match("(?ism).*?{([a-z0-9.]+)(:.*?)?}", line):
                    for var in re.findall("(?ism).*?({([a-z0-9.]+)(:.*?)?})", line):
                        lookup: str = var[0][1:-1]
                        if ":" in lookup:
                            lookup = lookup[:lookup.index(":")]
                        result = eval(lookup, state)
                        if result is None:
                            result = ""
                        else:
                            result = f":{result}"
                        line = line.replace(var[0], "{" + f"{lookup}{result}" + "}")
                section.text.append(line)

        if 'player' in state:
            is_dead = eval("player.hp == 0", state)
            if is_dead:
                section.text.append(f";## ---> PLAYER IS DEAD <---")
                section.text.append(f"")
            else:
                player: CharacterSheet = state["player"]
                has_mana: bool = player.mana > 0
                moderately_injured: bool = player.hp <= player.hit_points_max // 2
                severely_injured: bool = player.hp <= player.hit_points_max // 3
                injured: bool = player.hp <= (player.hit_points_max * 2) // 3
                lightly_injured: bool = player.hp <= (player.hit_points_max * 4) // 5
                has_item: bool = player.has_item('ointment')
                has_item = player.has_item('heal') or has_item
                has_item = player.has_item('vitality') or has_item
                needs_healing: str = f" AND NEEDS HEALING [mana: {has_mana}, item: {has_item}]" if has_mana or has_item else ""
                if severely_injured:
                    section.text.append(f";## ---> PLAYER IS GRAVELY WOUNDED{needs_healing} (HP: {player.hp}) <---")
                elif moderately_injured:
                    section.text.append(f";## ---> PLAYER IS BADLY INJURED{needs_healing} (HP: {player.hp}) <---")
                elif injured:
                    section.text.append(f";## ---> PLAYER IS INJURED{needs_healing} (HP: {player.hp}) <---")
                elif lightly_injured:
                    section.text.append(f";## ---> PLAYER IS LIGHTLY INJURED{needs_healing} (HP: {player.hp}) <---")
                section.text.append(f"")

        # determine child sections and clone environment into children
        for choice in section.choices:
            if choice.label not in sections_by_label:
                raise Exception(f"{choice.label} not in sections_by_label")
            if choice.label in sections_by_label:
                location: str = ""
                if 'location' in state:
                    location = state['location']
                location = f" ({location})" if location else ''
                child_section = sections_by_label[choice.label]
                child_section.rooms = eval(f"save_rooms()", state)
                child_section.path = section.path.copy()
                child_section.path.append(f"{section.name}|{section.label}{location}")
                child_section.state = state

    # sections[1:] = sorted(sections[1:], key=lambda x: (1 if x.choices else 2, x.label))
    have_choices: int = 0
    not_have_choices: int =0
    with open(gb_file, "w") as w:
        w.write(str(meta_header))
        sections_have.clear()
        for section in sections:
            if section.label in sections_have:
                continue
            sections_have.add(section.label)
            w.write(str(section))
            if section.choices:
                have_choices += 1
            else:
                not_have_choices += 1
        new_sections.sort(key=lambda x: x.label)
        for section in new_sections:
            w.write(str(section))
    print()
    total_choices = have_choices + not_have_choices
    have_pct: int = (100*have_choices) // total_choices
    not_have_pct: int = (100 * not_have_choices) // total_choices
    print(f"Have choices: {have_choices:,} ({have_pct:02}%)."
          f" Need choices added: {not_have_choices:,} ({not_have_pct:02}%).")
    print()

    with open(html_file, "w") as w:
        w.write("<html><meta charset='utf-8'/>\n")
        w.write(f"<head><title>{Section.escape_html(meta_header.title)}</title></head>\n")
        w.write("<body style='fonts-size: 200%;'>")
        w.write(meta_header.html())
        sections_have.clear()
        sections[1:].sort(key=lambda sec: sec.name)
        for section in sections:
            if section.label in sections_have:
                continue
            sections_have.add(section.label)
            w.write(section.html())
        w.write("\n</body></html>\n")


if __name__ == "__main__":
    main()
    print()
