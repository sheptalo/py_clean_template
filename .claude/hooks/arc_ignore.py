import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

MARKER = re.compile(r"#\s*arc:\s*ignore")


def _marked_lines(text: str) -> Counter[str]:
    return Counter(line.strip() for line in text.splitlines() if MARKER.search(line))


def _added_marked_lines(tool_name: str, tool_input: dict[str, Any], cwd: str) -> Counter[str]:
    match tool_name:
        case "Bash":
            return _marked_lines(tool_input["command"])
        case "Write":
            path = Path(cwd, tool_input["file_path"])
            old = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
            return _marked_lines(tool_input["content"]) - _marked_lines(old)
        case "Edit":
            return _marked_lines(tool_input["new_string"]) - _marked_lines(tool_input["old_string"])
        case "MultiEdit":
            added: Counter[str] = Counter()
            for edit in tool_input["edits"]:
                added += _marked_lines(edit["new_string"]) - _marked_lines(edit["old_string"])
            return added
        case _:
            return Counter()


def main() -> None:
    payload = json.load(sys.stdin)
    added = _added_marked_lines(payload["tool_name"], payload["tool_input"], payload["cwd"])
    if not added:
        return

    reason = (
        "Агенту запрещено добавлять, изменять или переносить arc: ignore (см. AGENTS.md), "
        "даже по просьбе пользователя. Исправь код так, чтобы проверка из scripts/ проходила. "
        "Если это невозможно — остановись и опиши пользователю нарушение и правило. "
        "Для поиска существующих комментариев используй Grep вместо Bash."
    )
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
