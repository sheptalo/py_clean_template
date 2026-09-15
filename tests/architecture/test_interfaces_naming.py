from tests.architecture._project import find_package_dir, is_ignored, iter_classdefs, source_files

RULE = "interfaces-naming"


def _is_interface_name(name: str) -> bool:
    return len(name) > 1 and name[0] == "I" and name[1].isupper()


def test_interfaces_are_prefixed_with_i() -> None:
    package = find_package_dir()
    paths = source_files(package / "application" / "interfaces")

    violations = [
        f"{path.relative_to(package)}:{node.name}"
        for path, node in iter_classdefs(paths)
        if not _is_interface_name(node.name) and not is_ignored(path, node.lineno, RULE)
    ]

    assert not violations, (
        f"Every class under application/interfaces must be named like IUseCase (I + PascalCase): {violations}"
    )
