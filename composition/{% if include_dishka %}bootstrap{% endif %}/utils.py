import importlib
import pkgutil
from types import ModuleType


def get_children(cls: type) -> list[type]:
    children: list[type] = []
    for klass in cls.__subclasses__():
        children.append(klass)
        children.extend(get_children(klass))
    return children


def load_packages(package: ModuleType) -> None:
    if not hasattr(package, "__path__"):
        return
    for _, module_name, _ in pkgutil.walk_packages(
        package.__path__, prefix=package.__name__ + "."
    ):
        module = importlib.import_module(module_name)
        load_packages(module)
