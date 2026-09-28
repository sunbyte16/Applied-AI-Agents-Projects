"""
PromptLab AI - LLM Service Integration
Handles OpenAI / OpenAI-compatible API interactions, timing, token accounting,
safe exception mapping, and output formatting.
"""

import time
import logging
from typing import Optional
import openai
from openai import OpenAI

from backend import config
from backend.models import (
    GenerateRequest,
    GenerateResponse,
    CompareRequest,
    CompareResponse,
    PromptStrategy,
    PromptInspectorData,
    TokenUsage,
)
from backend.prompt_engine import (
    assemble_prompt,
    parse_and_validate_json_response,
)

logger = logging.getLogger("promptlab.llm_service")


def get_openai_client() -> Optional[OpenAI]:
    """Instantiate and return OpenAI client if key is configured, else None."""
    if not config.is_api_key_configured():
        return None

    client_kwargs = {
        "api_key": config.ACTIVE_API_KEY,
        "timeout": config.REQUEST_TIMEOUT_SECONDS,
    }
    if config.OPENAI_BASE_URL:
        client_kwargs["base_url"] = config.OPENAI_BASE_URL

    return OpenAI(**client_kwargs)


def generate_completion(request: GenerateRequest) -> GenerateResponse:
    """
    Executes a real LLM generation request with full prompt assembly,
    API calling, timing, error resilience, and structured validation.
    """
    system_prompt, user_prompt = assemble_prompt(request)
    selected_model = request.model or config.DEFAULT_MODEL
    temperature = request.temperature if request.temperature is not None else config.DEFAULT_TEMPERATURE

    inspector_data = PromptInspectorData(
        system_prompt=system_prompt,
        generated_prompt=user_prompt,
        strategy=request.strategy.value,
        output_format=request.output_format or ("Structured JSON" if request.strategy == PromptStrategy.STRUCTURED else "Markdown/Text"),
        model_settings={
            "model": selected_model,
            "temperature": temperature,
            "max_input_length": config.MAX_INPUT_LENGTH,
        }
    )

    client = get_openai_client()
    if not client:
        return GenerateResponse(
            success=False,
            response="LLM API key is not configured. Please set OPENAI_API_KEY in your .env file to enable live completions.",
            strategy=request.strategy.value,
            model=selected_model,
            structured=False,
            prompt_inspector=inspector_data,
            error="API_KEY_MISSING: OPENAI_API_KEY not found or set to placeholder in .env"
        )

    start_time = time.perf_counter()

    try:
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Call the OpenAI Chat Completions API
        completion_args = {
            "model": selected_model,
            "messages": messages,
            "temperature": temperature,
        }

        # If structured strategy and OpenAI supports response_format
        if request.strategy == PromptStrategy.STRUCTURED and "gpt" in selected_model.lower():
            try:
                # Add json_object response format if model supports it
                completion_args["response_format"] = {"type": "json_object"}
            except Exception:
                pass  # Graceful fallback for non-supporting models

        completion = client.chat.completions.create(**completion_args)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        raw_output = completion.choices[0].message.content or ""

        # Extract usage data
        usage_data = None
        if completion.usage:
            usage_data = TokenUsage(
                prompt_tokens=completion.usage.prompt_tokens or 0,
                completion_tokens=completion.usage.completion_tokens or 0,
                total_tokens=completion.usage.total_tokens or 0,
            )

        # Handle Structured Output validation
        is_structured = False
        parsed_json = None
        validation_error = None

        if request.strategy == PromptStrategy.STRUCTURED:
            is_valid, parsed_obj, v_err = parse_and_validate_json_response(raw_output)
            is_structured = is_valid
            parsed_json = parsed_obj
            validation_error = v_err

        return GenerateResponse(
            success=True,
            response=raw_output,
            strategy=request.strategy.value,
            model=selected_model,
            structured=is_structured,
            parsed_json=parsed_json,
            validation_error=validation_error,
            prompt_inspector=inspector_data,
            usage=usage_data,
            latency_ms=latency_ms,
            error=None
        )

    except openai.AuthenticationError as err:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(f"Authentication error: {err}")
        return GenerateResponse(
            success=False,
            response="Authentication failed. Please verify that your OPENAI_API_KEY in .env is valid and active.",
            strategy=request.strategy.value,
            model=selected_model,
            prompt_inspector=inspector_data,
            latency_ms=latency_ms,
            error="AUTHENTICATION_FAILED: Invalid API Key"
        )

    except openai.RateLimitError as err:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(f"Rate limit error: {err}")
        return GenerateResponse(
            success=False,
            response="Rate limit or quota reached on the LLM API. Please wait a moment or check your account usage quota.",
            strategy=request.strategy.value,
            model=selected_model,
            prompt_inspector=inspector_data,
            latency_ms=latency_ms,
            error="RATE_LIMIT_EXCEEDED: Quota or burst limit reached"
        )

    except openai.APITimeoutError as err:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(f"API Timeout error: {err}")
        return GenerateResponse(
            success=False,
            response=f"The LLM API request timed out after {config.REQUEST_TIMEOUT_SECONDS} seconds.",
            strategy=request.strategy.value,
            model=selected_model,
            prompt_inspector=inspector_data,
            latency_ms=latency_ms,
            error="REQUEST_TIMEOUT: Model response took too long"
        )

    except openai.APIConnectionError as err:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(f"Connection error: {err}")
        return GenerateResponse(
            success=False,
            response="Unable to establish a connection to the LLM API. Please check your network connection or API endpoint.",
            strategy=request.strategy.value,
            model=selected_model,
            prompt_inspector=inspector_data,
            latency_ms=latency_ms,
            error="CONNECTION_ERROR: Failed to reach API server"
        )

    except openai.BadRequestError as err:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(f"Bad request error: {err}")
        clean_msg = str(err.message) if hasattr(err, "message") else str(err)
        return GenerateResponse(
            success=False,
            response=f"The LLM API rejected the request parameters: {clean_msg}",
            strategy=request.strategy.value,
            model=selected_model,
            prompt_inspector=inspector_data,
            latency_ms=latency_ms,
            error=f"BAD_REQUEST: {clean_msg}"
        )

    except Exception as err:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.exception("Unexpected error during LLM generation")
        return GenerateResponse(
            success=False,
            response="An unexpected server error occurred while contacting the LLM service. Please try again.",
            strategy=request.strategy.value,
            model=selected_model,
            prompt_inspector=inspector_data,
            latency_ms=latency_ms,
            error=f"INTERNAL_ERROR: {type(err).__name__}"
        )


def compare_strategies(request: CompareRequest) -> CompareResponse:
    """
    Executes and compares two distinct prompting strategies side-by-side
    for the exact same user input and parameters.
    """
    req_a = GenerateRequest(
        user_input=request.user_input,
        strategy=request.strategy_a,
        role=request.role,
        objective=request.objective,
        context=request.context,
        constraints=request.constraints,
        output_format=request.output_format,
        model=request.model,
        temperature=request.temperature
    )

    req_b = GenerateRequest(
        user_input=request.user_input,
        strategy=request.strategy_b,
        role=request.role,
        objective=request.objective,
        context=request.context,
        constraints=request.constraints,
        output_format=request.output_format,
        model=request.model,
        temperature=request.temperature
    )

    res_a = generate_completion(req_a)
    res_b = generate_completion(req_b)

    return CompareResponse(
        success=(res_a.success and res_b.success),
        result_a=res_a,
        result_b=res_b
    )
