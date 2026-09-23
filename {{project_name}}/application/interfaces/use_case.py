from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import dataclass_transform


class IUseCase[Input, Output](ABC):
    @abstractmethod
    async def __call__(self, data: Input) -> Output: ...


@dataclass_transform(frozen_default=True, eq_default=False)
def use_case[T](cls: type[T]) -> type[T]:
    return dataclass(frozen=True, eq=False)(cls)
