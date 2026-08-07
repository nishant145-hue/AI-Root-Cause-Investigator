import logging
import time

from app.core.config import settings
from app.exceptions.ai_exceptions import AIConnectionError
from groq import (
    APIConnectionError,
    APIStatusError,
    Groq,
    RateLimitError,
)

logger = logging.getLogger(__name__)

class GroqClient:

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to Groq with retry logic.
        """

        last_exception = None

        for attempt in range(settings.GROQ_MAX_RETRIES):

            try:
                logger.info(
                    "Sending request to Groq model '%s'.",
                    self.model,
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                        messages=[
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                    temperature=0,
                )
                logger.info(
                    "Groq response received successfully."
                )
                return response.choices[0].message.content

            except (
                RateLimitError,
                APIConnectionError,
                APIStatusError,
            ) as exc:

                last_exception = exc

                if attempt == settings.GROQ_MAX_RETRIES - 1:
                    break

                delay = settings.GROQ_RETRY_DELAY * (2 ** attempt)
                
                logger.warning(
                    "Groq request failed (attempt %d/%d). "
                    "Retrying in %d seconds.",
                    attempt + 1,
                    settings.GROQ_MAX_RETRIES,
                    delay,
                )
                
                time.sleep(delay)
                
                logger.error(
                    "Groq request failed after %d attempts.",
                    settings.GROQ_MAX_RETRIES,
                )

        raise AIConnectionError(
            "Failed to communicate with Groq after multiple retries."
        ) from last_exception