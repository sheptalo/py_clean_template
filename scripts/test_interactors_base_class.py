from scripts._project import (
    base_name,
    find_package_dir,
    is_ignored,
    iter_classdefs,
    source_files,
)

RULE = "interactor-base-class"


def test_interactors_subclass_iinteractor() -> None:
    package = find_package_dir()
    paths = source_files(package / "application" / "interactors")

    violations = [
        f"{path.relative_to(package)}:{node.name}"
        for path, node in iter_classdefs(paths)
        if "IInteractor" not in {base_name(base) for base in node.bases} and not is_ignored(path, node.lineno, RULE)
    ]

    assert not violations, f"Every class in application/interactors must subclass IInteractor: {violations}"
