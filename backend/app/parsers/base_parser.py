from abc import ABC, abstractmethod

from app.schemas.parsed_log import ParsedLog


class BaseParser(ABC):

    @abstractmethod
    def parse(self, file_path: str) -> list[ParsedLog]:
        """
        Parse file into ParsedLog objects.
        """
        pass