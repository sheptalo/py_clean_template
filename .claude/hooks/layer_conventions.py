import json
import os
import sys
import tempfile
from pathlib import Path

LAYERS = ("domain", "application", "infrastructure", "presentation")


def _layer_init(file_path: Path, root: Path) -> Path | None:
    try:
        parts = file_path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return None

    match parts:
        case ("composition", _, *_):
            init = root / "composition" / "__init__.py"
        case (package, layer, _, *_) if layer in LAYERS:
            if not all((root / package / name).is_dir() for name in LAYERS):
                return None
            init = root / package / layer / "__init__.py"
        case _:
            return None

    return init.resolve() if init.is_file() else None


def _state_file(session_id: str) -> Path:
    directory = Path(tempfile.gettempdir()) / "claude-layer-conventions"
    directory.mkdir(exist_ok=True)
    return directory / session_id


def main() -> None:
    payload = json.load(sys.stdin)
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR", payload["cwd"]))
    file_path = Path(payload["cwd"], payload["tool_input"]["file_path"])
    init = _layer_init(file_path, root)
    if init is None:
        return

    state = _state_file(payload["session_id"])

    if payload["hook_event_name"] == "PostToolUse":
        if file_path.resolve() == init:
            with state.open("a", encoding="utf-8") as f:
                f.write(f"{init}\n")
        return

    already_read = state.is_file() and str(init) in (
        state.read_text(encoding="utf-8").splitlines()
    )
    if already_read:
        return

    reason = (
        f"Перед изменением {file_path.resolve().relative_to(root.resolve())} "
        f"прочитай конвенции слоя: {init.relative_to(root.resolve())}. "
        "Затем выбери слой по этим конвенциям и повтори изменение."
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
