"""Write rendered files, and the skeletons added to what a human already wrote."""

import ast
from functools import partial
from pathlib import Path

from tools.codegen.application import Skeleton
from tools.codegen.output import REPO_ROOT, format_codes
from tools.codegen.render import (
    application_renderers,
    dto_dir,
    find_package,
    generated_dir,
    interface_dir,
    is_generated,
    use_case_dir,
)
from tools.codegen.spec import SpecError


def parse_body(path: Path) -> list[ast.stmt]:
    if not path.is_file():
        return []
    try:
        return ast.parse(path.read_text(encoding="utf-8")).body
    except SyntaxError as error:
        raise SpecError(path, f"cannot be parsed: {error}") from error


def is_docstring(node: ast.stmt) -> bool:
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)


def extend(path: Path, body: list[ast.stmt], skeleton: Skeleton) -> str:
    """Put the new classes into what a human already wrote: imports on top, classes at the end."""
    if not body:
        return f"{skeleton.imports}\n\n{skeleton.code}\n"
    lines = path.read_text(encoding="utf-8").splitlines()
    at = (body[0].end_lineno or 0) if is_docstring(body[0]) else 0
    return "\n".join([*lines[:at], skeleton.imports, *lines[at:], "", skeleton.code]) + "\n"


def skeletons() -> dict[Path, str]:
    """Skeletons: the classes of the specification are added once, what is already written stays untouched."""
    package = find_package()
    files: dict[Path, str] = {}
    for path, renderer in application_renderers(package).items():
        targets = [
            (use_case_dir(package) / f"{path.stem}.py", renderer.render_use_cases),
            (REPO_ROOT / "tests" / "fakes" / f"{path.stem}.py", renderer.render_fakes),
        ]
        for module, subclasses in renderer.implementation_modules().items():
            target = (REPO_ROOT / package).joinpath(*module.split(".")).with_suffix(".py")
            targets.append((target, partial(renderer.render_subclasses, subclasses, settings=True)))
        for target, render in targets:
            body = parse_body(target)
            skeleton = render({node.name for node in body if isinstance(node, ast.ClassDef)})
            if skeleton is not None:
                files[target] = extend(target, body, skeleton)
    return files


def obsolete(package: str, files: dict[Path, str]) -> set[Path]:
    unknown = {path for path in generated_dir(package).glob("*.py") if path not in files and is_generated(path)}
    for directory in (dto_dir(package), interface_dir(package)):
        unknown |= {path for path in directory.glob("*.py") if path not in files and is_generated(path)}
    return unknown


def outdated(files: dict[Path, str]) -> list[Path]:
    package = find_package()
    changed = [path for path, text in files.items() if not path.is_file() or path.read_text(encoding="utf-8") != text]
    return sorted(obsolete(package, files) | set(changed))


def hand_written(files: dict[Path, str]) -> list[Path]:
    """Python files the generator is about to write that already exist and were not generated."""
    return [path for path in files if path.suffix == ".py" and path.is_file() and not is_generated(path)]


def write(files: dict[Path, str]) -> list[Path]:
    package = find_package()
    blocked = hand_written(files)
    if blocked:
        raise SpecError(
            blocked[0], "written by hand, the generator would overwrite it: rename the specification or move the file"
        )
    changed = outdated(files)
    created = skeletons()  # before anything is written: a broken file of the user stops the run with nothing touched
    for path in obsolete(package, files):
        path.unlink()
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    for path, text in format_codes(created).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return sorted(changed + list(created))
