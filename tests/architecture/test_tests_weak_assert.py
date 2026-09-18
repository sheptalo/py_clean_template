import ast

from tests.architecture._project import REPO_ROOT, is_ignored
from tests.architecture._tests import files_in, iter_functions

RULE = "tests-weak-assert"


def _is_weak(node: ast.Assert) -> bool:
    test = node.test
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        right = test.comparators[0]
        if isinstance(test.ops[0], ast.IsNot) and isinstance(right, ast.Constant) and right.value is None:
            return True
        if isinstance(test.ops[0], (ast.Gt, ast.GtE, ast.NotEq)) and isinstance(right, ast.Constant):
            return isinstance(test.left, ast.Call) and getattr(test.left.func, "id", None) == "len"
    return isinstance(test, ast.Call) and getattr(test.func, "id", None) == "isinstance"


def test_tests_assert_concrete_values() -> None:
    violations = []
    for path, node in iter_functions(files_in("domain", "application", "infrastructure", "presentation")):
        asserts = [child for child in ast.walk(node) if isinstance(child, ast.Assert)]
        if (
            node.name.startswith("test_")
            and asserts
            and all(_is_weak(child) for child in asserts)
            and not is_ignored(path, node.lineno, RULE)
        ):
            violations.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}:{node.name}")

    assert not violations, (
        f"A test asserts a concrete value, not only that something came back "
        f"(is not None, len(...) > 0, isinstance): {violations}"
    )
