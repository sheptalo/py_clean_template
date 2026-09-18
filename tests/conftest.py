from pathlib import Path

import pytest

INTEGRATION_TESTS = Path(__file__).parent / "infrastructure"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Tests of infrastructure need real services: mark them integration, so pre-commit leaves them out."""
    for item in items:
        if item.path.is_relative_to(INTEGRATION_TESTS):
            item.add_marker(pytest.mark.integration)
