import ast
import re
from collections.abc import Iterator
from pathlib import Path

from scripts._project import REPO_ROOT, is_ignored, iter_all_python_files, parse

FILE_RULE = "snake-case-file"
VARIABLE_RULE = "snake-case-variable"
_SNAKE = re.compile(r"^_{0,2}[a-z][a-z0-9_]*_{0,2}$")
_CONSTANT = re.compile(r"^_{0,2}[A-Z][A-Z0-9_]*_{0,2}$")


def _is_snake_case_or_constant(name: str) -> bool:
    return bool(_SNAKE.fullmatch(name) or _CONSTANT.fullmatch(name))


def _stem(path: Path) -> str:
    name = path.name
    for suffix in (".py.jinja", ".py"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _bad_variable_names(path: Path) -> Iterator[str]:
    rel = path.relative_to(REPO_ROOT)
    for node in ast.walk(parse(path)):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if (
                isinstance(target, ast.Name)
                and not _is_snake_case_or_constant(target.id)
                and not is_ignored(path, node.lineno, VARIABLE_RULE)
            ):
                yield f"{rel}:{node.lineno}:{target.id}"


def test_file_names_are_snake_case() -> None:
    violations = [
        str(path.relative_to(REPO_ROOT))
        for path in iter_all_python_files()
        if not _is_snake_case_or_constant(_stem(path)) and not is_ignored(path, 1, FILE_RULE)
    ]

    assert not violations, f"File names must be snake_case: {violations}"


def test_variable_names_are_snake_case() -> None:
    violations = [name for path in iter_all_python_files() for name in _bad_variable_names(path)]

    assert not violations, f"Variable names must be snake_case: {violations}"
