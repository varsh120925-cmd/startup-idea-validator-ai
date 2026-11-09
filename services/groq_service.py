import os
import json
import time
import logging
from config import Config

logger = logging.getLogger(__name__)

class GroqService:
    """Service to interact with Groq API for LLM reasoning and agent execution"""

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or Config.GROQ_API_KEY
        self.model = model or Config.GROQ_MODEL
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")
                self._client = None
        else:
            self._client = None

    def is_available(self):
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    def test_connection(self):
        """Test Groq API connection and return status tuple (success, message)"""
        if not self.is_available():
            return False, "Groq API Key is not set or empty."
        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Respond with 'OK'"}],
                max_tokens=5,
                temperature=0.1
            )
            content = response.choices[0].message.content
            return True, f"Groq Connected successfully! Response: {content}"
        except Exception as e:
            return False, f"Groq API connection error: {str(e)}"

    def chat_completion(self, messages, temperature=0.7, max_tokens=2048, json_mode=False):
        """
        Execute a chat completion with error handling and retry logic.
        Returns parsed dict if json_mode=True, or response string otherwise.
        """
        if not self.is_available():
            raise ValueError("GROQ_API_KEY is not configured.")

        from groq import Groq
        client = Groq(api_key=self.api_key)

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        retries = 2
        for attempt in range(retries):
            try:
                start_time = time.time()
                response = client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                elapsed = time.time() - start_time

                if json_mode:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        # Extract JSON snippet if wrapped in markdown
                        import re
                        match = re.search(r"\{.*\}", content, re.DOTALL)
                        if match:
                            return json.loads(match.group(0))
                        raise ValueError(f"Model did not return valid JSON: {content}")
                return content

            except Exception as e:
                logger.warning(f"Groq API attempt {attempt+1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(1.5)
                else:
                    raise e
