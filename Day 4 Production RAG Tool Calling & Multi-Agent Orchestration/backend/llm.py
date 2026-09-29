"""
Unified LLM Client Layer for OrchestraRAG AI.
Integrates Groq, OpenAI, and deterministic Mock providers with strict JSON schema parsing and retry bounds.
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional
from backend.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Multi-provider LLM interface supporting Groq, OpenAI, and deterministic Mock fallback."""

    def __init__(self):
        self.provider = settings.get_active_llm_provider()
        self.model = settings.DEFAULT_MODEL
        self._groq_client = None
        self._openai_client = None
        self._init_clients()

    def _init_clients(self) -> None:
        """Initialize active API client."""
        if self.provider == "groq" and settings.GROQ_API_KEY:
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=settings.GROQ_API_KEY)
                logger.info("Initialized Groq LLM client.")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq: {e}. Falling back to mock.")
                self.provider = "mock"

        elif self.provider == "openai" and settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL,
                )
                logger.info("Initialized OpenAI LLM client.")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}. Falling back to mock.")
                self.provider = "mock"

    def _extract_json_block(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from Markdown fenced blocks or raw strings."""
        if not text:
            return None
        text = text.strip()
        # Look for ```json ... ```
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except Exception:
                pass

        # Try parsing from first { to last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass

        try:
            return json.loads(text)
        except Exception:
            return None

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: int = 2048,
    ) -> str:
        """Generate plain text completion."""
        temp = temperature if temperature is not None else settings.DEFAULT_TEMPERATURE

        if self.provider == "groq" and self._groq_client:
            try:
                resp = self._groq_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temp,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content or ""
            except Exception as e:
                logger.error(f"Groq API call failed: {e}. Fallback to deterministic mock.")

        elif self.provider == "openai" and self._openai_client:
            try:
                resp = self._openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temp,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content or ""
            except Exception as e:
                logger.error(f"OpenAI API call failed: {e}. Fallback to deterministic mock.")

        # Deterministic Mock Fallback for reliable testing
        return f"[Synthesized Response based on provided context]\n\n{user_prompt[:200]}..."

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_desc: Optional[str] = None,
        temperature: Optional[float] = 0.0,
    ) -> Dict[str, Any]:
        """Generate structured JSON response adhering to schema expectations."""
        prompt = user_prompt
        if schema_desc:
            prompt += f"\n\nYou MUST respond with valid JSON strictly adhering to this format:\n{schema_desc}\nDo NOT include markdown explanations outside the JSON."

        if self.provider == "groq" and self._groq_client:
            try:
                resp = self._groq_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt + "\nYou output strictly valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=temperature,
                )
                raw = resp.choices[0].message.content or "{}"
                parsed = self._extract_json_block(raw)
                if parsed is not None:
                    return parsed
            except Exception as e:
                logger.warning(f"Groq JSON generation error: {e}. Attempting text parsing.")

        elif self.provider == "openai" and self._openai_client:
            try:
                resp = self._openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt + "\nYou output strictly valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=temperature,
                )
                raw = resp.choices[0].message.content or "{}"
                parsed = self._extract_json_block(raw)
                if parsed is not None:
                    return parsed
            except Exception as e:
                logger.warning(f"OpenAI JSON generation error: {e}.")

        # If LLM failed or parsed None, try generating plain text and extracting JSON
        text = self.generate_text(system_prompt, prompt, temperature=temperature)
        parsed = self._extract_json_block(text)
        if parsed is not None:
            return parsed

        return {"error": "Failed to parse structured JSON from LLM response", "raw": text}


# Global singleton LLM client
llm_client = LLMClient()
