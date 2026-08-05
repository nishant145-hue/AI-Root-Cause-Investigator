import yaml

from app.exceptions.parser_exceptions import ParserError
from app.parsers.base_parser import BaseParser
from app.preprocessing.cleaner import MessageCleaner
from app.preprocessing.severity import SeverityNormalizer
from app.schemas.parsed_log import ParsedLog


class YAMLParser(BaseParser):

    def parse(self, file_path):

        with open(file_path, encoding="utf-8") as file:
            try:
                data = yaml.safe_load(file)

            except yaml.YAMLError as e:
                raise ParserError(
                    f"Invalid YAML format: {e}"
            ) from e

            except Exception as e:
                raise ParserError(
                    f"Unable to parse YAML file: {e}"
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
                    raw_line=str(item),
                    metadata=item,
                    )
                )

            except Exception as e:
                raise ParserError(
                    f"Invalid YAML log structure: {e}"
            ) from e

        return logs