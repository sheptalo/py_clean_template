from tests.architecture._project import (
    base_name,
    find_package_dir,
    is_ignored,
    iter_classdefs,
    source_files,
)

RULE = "use-case-decorator"


def test_use_cases_are_decorated() -> None:
    package = find_package_dir()
    paths = source_files(package / "application" / "use_cases")

    violations = [
        f"{path.relative_to(package)}:{node.name}"
        for path, node in iter_classdefs(paths)
        if "use_case" not in {base_name(decorator) for decorator in node.decorator_list}
        and not is_ignored(path, node.lineno, RULE)
    ]

    assert not violations, (
        f"Every class in application/use_cases must be decorated with @use_case from "
        f"application.interfaces.use_case: {violations}"
    )
