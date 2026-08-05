from app.parsers.generic_parser import GenericParser
from app.parsers.json_parser import JSONParser
from app.parsers.log_parser import LogParser
from app.parsers.parser_detector import ParserDetector
from app.parsers.txt_parser import TXTParser
from app.parsers.yaml_parser import YAMLParser


class ParserFactory:

    @staticmethod
    def get_parser(filename: str):

        parser_type = ParserDetector.detect(filename)

        if parser_type == "json":
            return JSONParser()

        if parser_type == "yaml":
            return YAMLParser()

        if parser_type == "txt":
            return TXTParser()

        if parser_type == "log":
            return LogParser()
        
        if parser_type == "generic":
            return GenericParser()


        raise ValueError(f"Unsupported parser: {parser_type}")