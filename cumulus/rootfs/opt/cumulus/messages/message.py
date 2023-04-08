"""Common messages implementations."""
from abc import ABC, abstractmethod

class Message(ABC):
    @abstractmethod
    async def process(self, cumulus: 'Cumulus') -> None:
        pass


class NoOperationMessage(Message):
    """Just do nothing."""

    async def process(self, cumulus: 'Cumulus') -> None:
        pass
