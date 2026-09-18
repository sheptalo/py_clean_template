import ast

from tests.architecture._project import REPO_ROOT, is_ignored
from tests.architecture._tests import files_in, iter_functions

RULE = "tests-domain-sync"


def test_domain_tests_are_synchronous() -> None:
    violations = [
        f"{path.relative_to(REPO_ROOT)}:{node.lineno}:{node.name}"
        for path, node in iter_functions(files_in("domain"))
        if isinstance(node, ast.AsyncFunctionDef) and not is_ignored(path, node.lineno, RULE)
    ]

    assert not violations, f"tests/domain test plain objects, without async: {violations}"
