from app.exceptions.parser_exceptions import ParserError
from app.parsers.base_parser import BaseParser
from app.preprocessing.cleaner import MessageCleaner
from app.schemas.parsed_log import ParsedLog


class TXTParser(BaseParser):

    def parse(self, file_path):

        logs = []
        
        try:
            with open(file_path, encoding="utf-8") as file:
            
                for line in file:

                    line = line.strip()

                    if not line:
                        continue

                    logs.append(
                        ParsedLog(
                            message=MessageCleaner.clean(line),
                            raw_line=line,
                        )
                    )
                
        except Exception as e:

            raise ParserError(
                f"Unable to parse TXT file: {e}"
            ) from e
            
        return logs