import ast
import re
from collections.abc import Iterator
from functools import cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_LAYERS = ("domain", "application", "infrastructure", "presentation")
_ARC_IGNORE = re.compile(r"#\s*arc:\s*ignore\[([^\]]+)\]")


class PackageNotFoundError(RuntimeError):
    def __init__(self, root: Path) -> None:
        super().__init__(f"No package under {root} containing {_LAYERS}")


def find_package_dir() -> Path:
    for child in sorted(REPO_ROOT.iterdir()):
        if child.is_dir() and all((child / layer).is_dir() for layer in _LAYERS):
            return child
    raise PackageNotFoundError(REPO_ROOT)


def iter_python_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return [path for path in root.rglob("*.py") if "__pycache__" not in path.parts]


def iter_all_python_files() -> list[Path]:
    package = find_package_dir()
    roots = [
        package,
        REPO_ROOT / "composition",
        REPO_ROOT / "tests",
    ]
    files: list[Path] = []
    for root in roots:
        files.extend(iter_python_files(root))
    return files


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def iter_classdefs(
    paths: list[Path],
) -> Iterator[tuple[Path, ast.ClassDef]]:
    for path in paths:
        for node in ast.walk(parse(path)):
            if isinstance(node, ast.ClassDef):
                yield path, node


def base_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return base_name(node.value)
    return None


@cache
def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def is_ignored(path: Path, line: int, rule: str) -> bool:
    """Проверяет комментарий `# arc: ignore[rule, ...]` на строке нарушения.

    Для нарушений уровня файла (например, имя файла) строка — первая.
    """
    lines = _lines(path)
    if not 1 <= line <= len(lines):
        return False
    match = _ARC_IGNORE.search(lines[line - 1])
    return match is not None and rule in {name.strip() for name in match.group(1).split(",")}


def source_files(directory: Path) -> list[Path]:
    return [path for path in iter_python_files(directory) if path.name != "__init__.py"]
