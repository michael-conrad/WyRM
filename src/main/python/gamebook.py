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
import subprocess

import dice
from dataclasses import dataclass
from dataclasses import field


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
    text: list[str] = field(default_factory=list)
    choices: list[Choice] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)

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
        comments: str = ""
        for comment in self.comments:
            if not comment.strip() and comments and comments[-1] == "\n":
                continue
            comments += f"// {comment.lstrip()}\n"
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
        result: str = f"""[{self.name}|{self.label}]
{comments}
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

    def __str__(self) -> str:
        notes: str = ""
        for note in self.notes:
            notes += f"Note: {note}\n"
        result: str = f"""Title: {self.title}
Subtitle: {self.subtitle}
Author: {self.author}
License: {self.license}

{notes.rstrip()}

"""
        return re.sub("\n\n+", "\n\n", result)


def new_label(already: set[str]) -> str:
    label: str = f"{random.randint(0, 4294967296 - 1):08x}"
    if label not in already:
        already.add(label)
    return label


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
            # Stash comments
            if line.strip().startswith("//"):
                section.comments.append(line.strip()[line.find("//") + 2:])
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
                    print(str(choice))

    for section in sections:
        if section.choices:
            for choice in section.choices:
                if choice.label not in section_labels:
                    known_labels.add(choice.label)
                    new_section: Section = Section()
                    new_sections.append(new_section)
                    new_section.label = choice.label
                    new_section.name = choice.text
                    new_section.comments.append(f"{section.name}|{section.label}")
    print(f"Sections added: {len(new_sections):,}")

    for section in sections:
        if not section.choices:
            print(f"Section [{section.name}|{section.label}] has no choices.")

    # Handle processing instructions such as roll dice
    for section in sections:
        for _, line in enumerate(section.text):
            line = line.strip().lower()
            if not line.startswith("!"):
                continue
            cmd: str = line[line.find("!")+1:].strip()
            cmt: str = ""
            if "//" in cmd:
                cmt = cmd[cmd.find("//") + 2:].strip()
                cmd = cmd[:cmd.find("//") - 1].strip()
            if re.match("^\\dd\\d.*", cmd) and "=" not in cmd:
                while cmd[-1] == "t":
                    cmd = cmd[:-1].strip()
                result: str = dice.roll(f"({cmd}) t")
                section.text[_] = f"!{cmd} = {result} // {cmt}"

    with open(gb_file, "w") as w:
        w.write(str(meta_header))
        for section in sections:
            w.write(str(section))
        for section in new_sections:
            w.write(str(section))
    #  subprocess.run(["git", "commit", "-m", "autosave [after]", gb_file],  #
    #               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
