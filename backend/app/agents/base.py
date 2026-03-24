from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any

import litellm
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

_RATE_LIMIT_MAX_RETRIES = 5
_last_call_time: float = 0.0
_MIN_CALL_INTERVAL = 3.0


def _parse_retry_after(error_msg: str, default: float = 6.0) -> float:
    """Extract wait time from Groq rate-limit error messages."""
    match_mins = re.search(r"try again in (\d+)m([\d.]+)s", error_msg, re.IGNORECASE)
    if match_mins:
        return float(match_mins.group(1)) * 60 + float(match_mins.group(2)) + 1.0
    match_secs = re.search(r"try again in ([\d.]+)s", error_msg, re.IGNORECASE)
    if match_secs:
        return float(match_secs.group(1)) + 1.0
    return default


class BaseAgent:
    """Base class for all AnalystOS agents."""

    def __init__(
        self,
        name: str,
        model: str,
        system_prompt: str,
        output_schema: type[BaseModel] | None = None,
    ):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.output_schema = output_schema

    async def _call_llm(self, call_kwargs: dict[str, Any]) -> Any:
        """Call LiteLLM with automatic retry on rate-limit errors."""
        global _last_call_time
        for attempt in range(_RATE_LIMIT_MAX_RETRIES):
            now = time.time()
            elapsed = now - _last_call_time
            if elapsed < _MIN_CALL_INTERVAL:
                await asyncio.sleep(_MIN_CALL_INTERVAL - elapsed)
            try:
                _last_call_time = time.time()
                return await litellm.acompletion(**call_kwargs)
            except Exception as exc:
                exc_str = str(exc)
                is_rate_limit = "rate_limit" in exc_str.lower() or "rate limit" in exc_str.lower()
                if not is_rate_limit or attempt == _RATE_LIMIT_MAX_RETRIES - 1:
                    raise

                wait = _parse_retry_after(exc_str, default=6.0 * (attempt + 1))
                if wait > 120:
                    raise RuntimeError(
                        f"Daily token limit exhausted for {call_kwargs.get('model', 'unknown')}. "
                        f"Please wait ~{int(wait // 60)} minutes or switch to a model with higher limits."
                    ) from exc
                logger.warning(
                    "%s hit rate limit (attempt %d/%d), waiting %.1fs",
                    self.name, attempt + 1, _RATE_LIMIT_MAX_RETRIES, wait,
                )
                await asyncio.sleep(wait)
        raise RuntimeError("unreachable")

    async def run(self, messages: list[dict], **kwargs: Any) -> dict:
        """Call LiteLLM with structured output, track tokens, emit trace step."""
        api_key = self._resolve_api_key()
        call_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2),
        }
        if api_key:
            call_kwargs["api_key"] = api_key

        if self.output_schema:
            call_kwargs["response_format"] = {"type": "json_object"}

        last_error: Exception | None = None
        max_retries = 2 if self.output_schema else 0

        for attempt in range(max_retries + 1):
            start = time.perf_counter()
            response = await self._call_llm(call_kwargs)
            latency_ms = round((time.perf_counter() - start) * 1000, 1)

            usage = response.usage
            raw_content = response.choices[0].message.content or ""

            if not self.output_schema:
                return {
                    "output": raw_content,
                    "usage": {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                    },
                    "model": self.model,
                    "latency_ms": latency_ms,
                }

            try:
                parsed = self.output_schema.model_validate_json(raw_content)
                return {
                    "output": parsed,
                    "usage": {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                    },
                    "model": self.model,
                    "latency_ms": latency_ms,
                }
            except Exception as exc:
                last_error = exc
                if attempt < max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    repair_msg = {
                        "role": "user",
                        "content": (
                            f"Your previous response was not valid JSON matching the schema. "
                            f"Error: {exc}. Please return ONLY valid JSON."
                        ),
                    }
                    call_kwargs["messages"] = [*messages, {"role": "assistant", "content": raw_content}, repair_msg]

        raise ValueError(
            f"Agent '{self.name}' failed to produce valid {self.output_schema.__name__} "
            f"after {max_retries + 1} attempts: {last_error}"
        )

    def _build_messages(
        self,
        user_content: str,
        context: dict | None = None,
        skills: list[str] | None = None,
    ) -> list[dict]:
        """Build message list: system prompt (with optional skill injection) + user message."""
        system_parts = [self.system_prompt]

        if self.output_schema:
            schema_json = json.dumps(self.output_schema.model_json_schema(), indent=2)
            system_parts.append(
                f"\n\n## Required Output JSON Schema\n"
                f"You MUST respond with ONLY a JSON object that matches this schema exactly. "
                f"ALL fields are required unless marked optional.\n```json\n{schema_json}\n```"
            )

        if skills:
            system_parts.append("\n\n## Additional Skills\n" + "\n".join(f"- {s}" for s in skills))

        system_msg = {"role": "system", "content": "\n".join(system_parts)}

        user_parts = [user_content]
        if context:
            user_parts.append(f"\n\n## Context\n```json\n{json.dumps(context, default=str)}\n```")

        user_msg = {"role": "user", "content": "\n".join(user_parts)}
        return [system_msg, user_msg]

    def _resolve_api_key(self) -> str | None:
        model_lower = self.model.lower()
        if model_lower.startswith("groq/") or "groq" in model_lower:
            return settings.groq_api_key or None
        if "claude" in model_lower or "anthropic" in model_lower:
            return settings.anthropic_api_key or None
        if "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower:
            return settings.openai_api_key or None
        return None
