import ast
from collections.abc import Iterator
from pathlib import Path

from tests.architecture._project import REPO_ROOT, iter_python_files, parse


def files_in(*layers: str) -> list[Path]:
    return [path for layer in layers for path in iter_python_files(REPO_ROOT / "tests" / layer)]


def imported_modules(node: ast.stmt) -> Iterator[str]:
    if isinstance(node, ast.Import):
        yield from (alias.name for alias in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module is not None:
        yield node.module
        yield from (f"{node.module}.{alias.name}" for alias in node.names)


def iter_imports(paths: list[Path]) -> Iterator[tuple[Path, ast.stmt, str]]:
    for path in paths:
        for node in ast.walk(parse(path)):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for module in imported_modules(node):
                    yield path, node, module


def iter_functions(paths: list[Path]) -> Iterator[tuple[Path, ast.FunctionDef | ast.AsyncFunctionDef]]:
    for path in paths:
        for node in ast.walk(parse(path)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield path, node
