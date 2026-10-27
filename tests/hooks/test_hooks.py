import json
import subprocess
import sys
import uuid
from collections.abc import Mapping
from pathlib import Path

from tests.architecture._project import REPO_ROOT, find_package_dir

HOOKS = REPO_ROOT / ".claude" / "hooks"
PACKAGE = find_package_dir()
MARK = "# arc" + ": ignore[snake-case-variable]"


def decision(hook: str, payload: dict[str, object]) -> str:
    """What a hook answers for one tool call: "allow", or the permission decision it refuses with."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(HOOKS / hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    if not result.stdout.strip():
        return "allow"
    return str(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"])


def layer_decision(event: str, tool: str, tool_input: Mapping[str, str], session: str) -> str:
    payload: dict[str, object] = {
        "hook_event_name": event,
        "tool_name": tool,
        "tool_input": tool_input,
        "cwd": str(REPO_ROOT),
        "session_id": session,
    }
    return decision("layer_conventions.py", payload)


def read_layer_init(session: str, layer: str) -> None:
    layer_decision("PostToolUse", "Read", {"file_path": str(PACKAGE / layer / "__init__.py")}, session)


def test_layer_hook_refuses_a_command_writing_into_an_unread_layer() -> None:
    session = str(uuid.uuid4())
    read_layer_init(session, "application")
    command = f"cp {PACKAGE.name}/application/a.py {PACKAGE.name}/infrastructure/b.py"

    assert layer_decision("PreToolUse", "Bash", {"command": command}, session) == "deny"


def test_layer_hook_allows_an_edit_in_a_layer_already_read() -> None:
    session = str(uuid.uuid4())
    read_layer_init(session, "application")
    edit = {"file_path": str(PACKAGE / "application" / "a.py"), "old_string": "a", "new_string": "b"}

    assert layer_decision("PreToolUse", "Edit", edit, session) == "allow"


def test_layer_hook_refuses_a_shell_redirect_into_an_unread_layer() -> None:
    command = f"echo done > {PACKAGE.name}/domain/x.py"

    assert layer_decision("PreToolUse", "Bash", {"command": command}, str(uuid.uuid4())) == "deny"


def test_layer_hook_allows_a_read_only_search_for_an_arrow() -> None:
    command = f'grep -n "->" {PACKAGE.name}/domain/x.py'

    assert layer_decision("PreToolUse", "Bash", {"command": command}, str(uuid.uuid4())) == "allow"


def arc_decision(tool: str, tool_input: Mapping[str, object], cwd: Path) -> str:
    return decision("arc_ignore.py", {"tool_name": tool, "tool_input": tool_input, "cwd": str(cwd)})


def test_arc_hook_allows_an_unrelated_edit(tmp_path: Path) -> None:
    probe = tmp_path / "probe.py"
    probe.write_text(f"a = 1  {MARK}\nb = 2\n", encoding="utf-8")
    edit = {"file_path": str(probe), "old_string": "b = 2", "new_string": "b = 3"}

    assert arc_decision("Edit", edit, tmp_path) == "allow"


def test_arc_hook_allows_an_edit_above_the_comment(tmp_path: Path) -> None:
    probe = tmp_path / "probe.py"
    probe.write_text(f"a = 1  {MARK}\nb = 2\n", encoding="utf-8")
    edit = {"file_path": str(probe), "old_string": f"a = 1  {MARK}", "new_string": f"c = 0\na = 1  {MARK}"}

    assert arc_decision("Edit", edit, tmp_path) == "allow"


def test_arc_hook_refuses_moving_the_comment(tmp_path: Path) -> None:
    probe = tmp_path / "probe.py"
    probe.write_text(f"a = 1  {MARK}\nb = 2\n", encoding="utf-8")
    edit = {"file_path": str(probe), "old_string": f"a = 1  {MARK}\nb = 2", "new_string": f"b = 2\na = 1  {MARK}"}

    assert arc_decision("Edit", edit, tmp_path) == "deny"


def test_arc_hook_refuses_a_new_file_with_the_comment(tmp_path: Path) -> None:
    write = {"file_path": str(tmp_path / "new.py"), "content": f"x = 1  {MARK}\n"}

    assert arc_decision("Write", write, tmp_path) == "deny"


def test_arc_hook_refuses_a_shell_command_that_writes_the_comment(tmp_path: Path) -> None:
    command = f"echo '{MARK}' >> notes.py"

    assert arc_decision("Bash", {"command": command}, tmp_path) == "deny"
