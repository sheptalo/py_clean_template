import json
import re
import sys
from pathlib import Path
from typing import Any

from _deny import deny

MARKER = re.compile(r"#\s*arc:\s*ignore")
SOURCE = (".py", ".py.jinja")


def _is_source(name: str) -> bool:
    return name.endswith(SOURCE)


def _marks(text: str) -> list[tuple[str, int, int]]:
    """Each ignore comment with its text, its line number from the top and its line number from the bottom."""
    lines = text.splitlines()
    return [(line.strip(), index, len(lines) - index) for index, line in enumerate(lines) if MARKER.search(line)]


def _new_text(tool_name: str, tool_input: dict[str, Any], old: str) -> str:
    if tool_name == "Write":
        return tool_input["content"]
    text = old
    for edit in tool_input.get("edits", [tool_input]):
        text = text.replace(edit["old_string"], edit["new_string"], -1 if edit.get("replace_all") else 1)
    return text


def _changes_marks(tool_name: str, tool_input: dict[str, Any], cwd: str) -> bool:
    if tool_name == "Bash":
        command = tool_input["command"]
        return bool(_marks(command)) and any(_is_source(word) for word in command.split())
    if not _is_source(tool_input.get("file_path", "")):
        return False
    path = Path(cwd, tool_input["file_path"])
    old = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    before = _marks(old)
    after = _marks(_new_text(tool_name, tool_input, old))
    if [text for text, _, _ in before] != [text for text, _, _ in after]:
        return True
    # An insert above moves a comment from the top only, an insert below from the bottom only: a move moves both.
    return any(b[1] != a[1] and b[2] != a[2] for b, a in zip(before, after, strict=True))


def main() -> None:
    payload = json.load(sys.stdin)
    if not _changes_marks(payload["tool_name"], payload["tool_input"], payload["cwd"]):
        return

    deny(
        "An agent may never add, change or move arc: ignore (see AGENTS.md), not even when the user "
        "asks. Fix the code so the check from tests/architecture/ passes. If that is impossible, stop "
        "and describe the violation and the rule to the user. To look for existing comments use Grep "
        "instead of Bash."
    )


if __name__ == "__main__":
    main()
