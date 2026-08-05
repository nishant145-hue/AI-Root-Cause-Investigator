from app.parsers.base_parser import BaseParser
from app.preprocessing.cleaner import MessageCleaner
from app.schemas.parsed_log import ParsedLog


class GenericParser(BaseParser):

    def parse(self, file_path):

        logs = []

        with open(file_path, encoding="utf-8", errors="ignore") as file:

            for line in file:

                line = line.strip()

                if line:

                    logs.append(
                        ParsedLog(
                            message=MessageCleaner.clean(line),
                            raw_line=line,
                        )
                    )

        return logs