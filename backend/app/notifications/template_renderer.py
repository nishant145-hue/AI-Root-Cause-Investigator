from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


TEMPLATE_DIR = Path(__file__).parent / "templates"


class NotificationTemplateRenderer:
    """Render notification templates using Jinja2."""

    def __init__(self) -> None:
        self.environment = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=select_autoescape(
                enabled_extensions=("html", "xml"),
            ),
        )

    def render(
        self,
        template_name: str,
        **context: Any,
    ) -> str:
        """Render a notification template."""

        template = self.environment.get_template(
            template_name
        )

        return template.render(**context)