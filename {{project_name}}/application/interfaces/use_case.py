from abc import ABC, abstractmethod
from dataclasses import dataclass


class IUseCase[Input, Output](ABC):
    @abstractmethod
    async def __call__(self, data: Input) -> Output: ...


use_case = dataclass(frozen=True, eq=False, slots=True)
