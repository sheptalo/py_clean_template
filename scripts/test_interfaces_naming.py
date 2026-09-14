from scripts._project import find_package_dir, iter_classdefs, source_files


def _is_interface_name(name: str) -> bool:
    return len(name) > 1 and name[0] == "I" and name[1].isupper()


def test_interfaces_are_prefixed_with_i() -> None:
    package = find_package_dir()
    paths = source_files(package / "application" / "interfaces")

    violations = [
        f"{path.relative_to(package)}:{node.name}"
        for path, node in iter_classdefs(paths)
        if not _is_interface_name(node.name)
    ]

    assert not violations, (
        "Every class under application/interfaces must be named like "
        f"IInteractor (I + PascalCase): {violations}"
    )
