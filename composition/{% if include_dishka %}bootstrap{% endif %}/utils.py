import importlib
import pkgutil
from types import ModuleType


class DuplicateRegistrationError(TypeError):
    """Two classes found by a scan claim the same DI key."""

    def __init__(self, first: type, second: type, conflict: str) -> None:
        super().__init__(
            f"{first.__module__}.{first.__qualname__} and {second.__module__}.{second.__qualname__} {conflict}"
        )


def get_children[T](cls: type[T]) -> list[type[T]]:
    """Every subclass once, however many paths of multiple inheritance lead to it."""
    children: list[type[T]] = []
    for klass in cls.__subclasses__():
        children.append(klass)
        children.extend(get_children(klass))
    return list(dict.fromkeys(children))


def load_packages(package: ModuleType) -> None:
    if not hasattr(package, "__path__"):
        return
    for _, module_name, _ in pkgutil.walk_packages(package.__path__, prefix=package.__name__ + "."):
        module = importlib.import_module(module_name)
        load_packages(module)
