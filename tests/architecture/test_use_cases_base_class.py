from tests.architecture._project import (
    base_name,
    find_package_dir,
    is_ignored,
    iter_classdefs,
    source_files,
)

RULE = "use-case-base-class"


def test_use_cases_subclass_iusecase() -> None:
    package = find_package_dir()
    paths = source_files(package / "application" / "use_cases")

    violations = [
        f"{path.relative_to(package)}:{node.name}"
        for path, node in iter_classdefs(paths)
        if "IUseCase" not in {base_name(base) for base in node.bases} and not is_ignored(path, node.lineno, RULE)
    ]

    assert not violations, f"Every class in application/use_cases must subclass IUseCase: {violations}"
