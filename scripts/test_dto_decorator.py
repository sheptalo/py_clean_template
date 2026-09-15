import ast
from pathlib import Path

from scripts._project import (
    base_name,
    find_package_dir,
    is_ignored,
    iter_all_python_files,
    iter_classdefs,
    source_files,
)

RULE = "dto-decorator"


def _interactor_dto_names(package: Path) -> set[str]:
    paths = source_files(package / "application" / "interactors")

    names: set[str] = set()
    for _, node in iter_classdefs(paths):
        for base in node.bases:
            if not isinstance(base, ast.Subscript):
                continue
            if base_name(base) != "IInteractor":
                continue
            args = base.slice.elts if isinstance(base.slice, ast.Tuple) else [base.slice]
            names.update(a.id for a in args if isinstance(a, ast.Name))
    return names


def test_interactor_dtos_use_dto_decorator() -> None:
    package = find_package_dir()
    dto_names = _interactor_dto_names(package)
    if not dto_names:
        return

    is_decorated = {
        node.name: any(base_name(dec) == "dto" for dec in node.decorator_list) or is_ignored(path, node.lineno, RULE)
        for path, node in iter_classdefs(iter_all_python_files())
        if node.name in dto_names
    }

    missing = dto_names - is_decorated.keys()
    assert not missing, f"Interactor DTOs not found as classes: {missing}"

    violations = [name for name, decorated in is_decorated.items() if not decorated]
    assert not violations, (
        f"Interactor Input/Output DTOs must use the @dto decorator from application.interfaces.dto: {violations}"
    )
