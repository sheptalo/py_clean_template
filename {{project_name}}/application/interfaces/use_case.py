from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol, dataclass_transform


class IUseCase[Input, Output](Protocol):
    """A scenario. A use case subclasses it, so auto-wiring finds it; a fake only needs the same call."""

    @abstractmethod
    async def __call__(self, data: Input) -> Output: ...


@dataclass_transform(frozen_default=True, eq_default=False)
def use_case[T](cls: type[T]) -> type[T]:
    return dataclass(frozen=True, eq=False)(cls)
