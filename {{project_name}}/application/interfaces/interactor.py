from abc import ABC, abstractmethod
from dataclasses import dataclass


class IInteractor[Input, Output](ABC):
    @abstractmethod
    async def __call__(self, data: Input) -> Output: ...


interactor = dataclass(frozen=True, eq=False, slots=True)
