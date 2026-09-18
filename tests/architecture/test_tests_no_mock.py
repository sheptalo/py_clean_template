from tests.architecture._project import REPO_ROOT, is_ignored
from tests.architecture._tests import files_in, iter_functions, iter_imports

RULE = "tests-no-mock"
_MOCK_MODULES = ("unittest.mock", "mock", "pytest_mock")


def test_domain_and_application_tests_use_no_mocks() -> None:
    paths = files_in("domain", "application")

    violations = [
        f"{path.relative_to(REPO_ROOT)}:{node.lineno}:{module}"
        for path, node, module in iter_imports(paths)
        if module.startswith(_MOCK_MODULES) and not is_ignored(path, node.lineno, RULE)
    ]
    violations += [
        f"{path.relative_to(REPO_ROOT)}:{node.lineno}:mocker"
        for path, node in iter_functions(paths)
        if "mocker" in {argument.arg for argument in node.args.args} and not is_ignored(path, node.lineno, RULE)
    ]

    assert not violations, (
        f"tests/domain and tests/application do not use mocks: replace a port with its fake from tests/fakes: "
        f"{violations}"
    )
