"""HelloAgents MVP LLM client - based on the OpenAI-compatible API."""

import os
from typing import Optional

from openai import OpenAI
from dotenv import load_dotenv

from .exceptions import HelloAgentsException


class HelloAgentsLLM:
    """
    Minimal LLM client for HelloAgents.

    Design:
    - Keep one OpenAI-compatible client.
    - Prefer explicit arguments.
    - Fall back to environment variables when arguments are omitted.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        # !! 读取环境变量前先载入.env文件
        load_dotenv()

        self.model = model or os.getenv("LLM_MODEL_ID")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", "60"))

        missing = [
            name
            for name, value in {
                "model": self.model,
                "api_key": self.api_key,
                "base_url": self.base_url,
            }.items()
            if not value
        ]
        if missing:
            joined = ", ".join(missing)
            raise HelloAgentsException(f"Missing required LLM config: {joined}")

        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def invoke(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Call the LLM and return the complete response text."""
        temperature = kwargs.pop("temperature", self.temperature)
        max_tokens = kwargs.pop("max_tokens", self.max_tokens)

        request = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            request["max_tokens"] = max_tokens
        request.update(kwargs)

        try:
            response = self._client.chat.completions.create(**request)
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise HelloAgentsException(f"LLM call failed: {exc}") from exc
