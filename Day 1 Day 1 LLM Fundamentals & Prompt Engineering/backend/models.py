"""
PromptLab AI - Pydantic Request & Response Data Models
Enforces strict input validation, type safety, and clean API serialization.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class PromptStrategy(str, Enum):
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    ROLE = "role"
    STRUCTURED = "structured"
    EXPERT = "expert"


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class PromptInspectorData(BaseModel):
    system_prompt: str
    generated_prompt: str
    strategy: str
    output_format: str
    model_settings: Dict[str, Any]


class StructuredOutputPayload(BaseModel):
    summary: str
    key_points: List[str] = []
    examples: List[str] = []
    next_steps: List[str] = []


class GenerateRequest(BaseModel):
    user_input: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="The core user question, instruction, or task."
    )
    strategy: PromptStrategy = Field(
        default=PromptStrategy.ZERO_SHOT,
        description="Prompt engineering strategy to employ."
    )
    role: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional persona or role definition (e.g. 'Senior ML Engineer')."
    )
    objective: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Specific goal or primary deliverable."
    )
    context: Optional[str] = Field(
        default=None,
        max_length=1500,
        description="Background details, audience, or target environment."
    )
    constraints: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Rules, negative constraints, length limits, or tone specifications."
    )
    output_format: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Desired formatting specification (e.g., JSON schema, Markdown tables)."
    )
    model: Optional[str] = Field(
        default="gpt-4o-mini",
        description="Target model identifier."
    )
    temperature: Optional[float] = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Sampling temperature between 0.0 (deterministic) and 1.0 (creative)."
    )

    @field_validator("user_input")
    @classmethod
    def validate_user_input(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("User input cannot be empty or solely whitespace.")
        return cleaned


class GenerateResponse(BaseModel):
    success: bool
    response: str
    strategy: str
    model: str
    structured: bool = False
    parsed_json: Optional[Any] = None
    validation_error: Optional[str] = None
    prompt_inspector: Optional[PromptInspectorData] = None
    usage: Optional[TokenUsage] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class CompareRequest(BaseModel):
    user_input: str = Field(..., min_length=1, max_length=10_000)
    strategy_a: PromptStrategy = Field(default=PromptStrategy.ZERO_SHOT)
    strategy_b: PromptStrategy = Field(default=PromptStrategy.FEW_SHOT)
    role: Optional[str] = None
    objective: Optional[str] = None
    context: Optional[str] = None
    constraints: Optional[str] = None
    output_format: Optional[str] = None
    model: Optional[str] = "gpt-4o-mini"
    temperature: Optional[float] = 0.3

    @field_validator("user_input")
    @classmethod
    def validate_user_input(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("User input cannot be empty or solely whitespace.")
        return cleaned


class CompareResponse(BaseModel):
    success: bool
    result_a: GenerateResponse
    result_b: GenerateResponse


class HealthResponse(BaseModel):
    status: str
    has_api_key: bool
    default_model: str
    available_models: List[str]
    masked_key: str
