from abc import ABCMeta
from typing import ClassVar, Literal


class IPort(metaclass=ABCMeta):  # noqa: B024 - Architecture based component
    scope: ClassVar[Literal["request", "app"]] = "request"
