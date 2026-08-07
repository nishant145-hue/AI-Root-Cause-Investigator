import json

from pydantic import ValidationError

from app.exceptions.parser_exceptions import ParserError
from app.parsers.base_parser import BaseParser
from app.preprocessing.cleaner import MessageCleaner
from app.preprocessing.severity import SeverityNormalizer
from app.schemas.parsed_log import ParsedLog


class JSONParser(BaseParser):

    def parse(self, file_path: str) -> list[ParsedLog]:

        with open(file_path, encoding="utf-8") as file:

            content = file.read()

            try:
                data = json.loads(content)

            except json.JSONDecodeError as e:
                raise ParserError(
                    f"Invalid JSON format: {e.msg} "
                    f"(line {e.lineno}, column {e.colno})"
                ) from e

            except Exception as e:
                raise ParserError(
                    f"Unable to parse JSON file: {e}"
                ) from e

        if isinstance(data, dict):
            data = [data]

        logs = []

        for item in data:
            try:
                logs.append(
                    ParsedLog(
                        timestamp=item.get("timestamp"),
                        severity=SeverityNormalizer.normalize(
                            item.get("level")
                        ),
                        message=MessageCleaner.clean(
                            item.get("message")
                        ),
                        raw_line=json.dumps(item),
                        metadata=item,
                    )
                )

            except ValidationError as e:
                raise ParserError(
                    f"Invalid log entry: {e}"
                ) from e

        return logs