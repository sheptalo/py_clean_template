import json
import re
import sys
import tempfile
from pathlib import Path

LAYERS = ("domain", "application", "infrastructure", "presentation")
WRITES = (">", "tee ", "sed -i", "cp ", "mv ", "touch ", "write_text", "dd ")
_PYTHON_FILE = re.compile(r"[\w./{}%-]+\.py")


def _targets(tool_input: dict[str, str], cwd: str, *, writes_only: bool) -> list[Path]:
    """The files a tool call touches: the argument of Edit/Write/Read, or the paths a Bash command names."""
    if "file_path" in tool_input:
        return [Path(cwd, tool_input["file_path"])]
    command = tool_input.get("command", "")
    if writes_only and not any(marker in command for marker in WRITES):
        return []
    return [Path(cwd, name) for name in _PYTHON_FILE.findall(command)]


def _root_of(file_path: Path) -> Path | None:
    """The project the file belongs to: the nearest ancestor holding pyproject.toml."""
    return next((parent for parent in file_path.resolve().parents if (parent / "pyproject.toml").is_file()), None)


def _layer_init(file_path: Path, root: Path) -> Path | None:
    parts = file_path.resolve().relative_to(root).parts

    match parts:
        case ("composition", _, *_):
            init = root / "composition" / "__init__.py"
        case ("tests", _, *_):
            init = root / "tests" / "__init__.py"
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
    post = payload["hook_event_name"] == "PostToolUse"
    targets = _targets(payload["tool_input"], payload["cwd"], writes_only=not post)
    found = [
        (path, root, init)
        for path in targets
        if (root := _root_of(path)) is not None and (init := _layer_init(path, root)) is not None
    ]
    if not found:
        return
    file_path, root, init = found[0]

    state = _state_file(payload["session_id"])

    if post:
        with state.open("a", encoding="utf-8") as f:
            f.writelines(f"{init}\n" for path, _, init in found if path.resolve() == init)
        return

    already_read = state.is_file() and str(init) in (state.read_text(encoding="utf-8").splitlines())
    if already_read:
        return

    reason = (
        f"Before changing {file_path.resolve().relative_to(root)}, read the conventions of its layer: "
        f"{init.relative_to(root)}. Then pick the layer by those conventions and repeat the change."
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
