"""
PromptLab AI - Test Suite
Covers Prompt Engine strategies, delimiters, input validation, JSON parsing,
and API endpoint responses.
"""

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from backend.models import GenerateRequest, PromptStrategy
from backend.prompt_engine import (
    SYSTEM_PROMPT,
    build_zero_shot_prompt,
    build_few_shot_prompt,
    build_role_prompt,
    build_structured_prompt,
    build_expert_prompt,
    assemble_prompt,
    parse_and_validate_json_response,
)
from backend.main import app

client = TestClient(app)


# ==============================================================================
# 1. Input Validation Tests
# ==============================================================================

def test_empty_user_input_rejected():
    """Verify that empty strings or whitespace-only inputs trigger validation errors."""
    with pytest.raises(ValidationError):
        GenerateRequest(user_input="")

    with pytest.raises(ValidationError):
        GenerateRequest(user_input="   \n\t  ")


def test_excessive_user_input_rejected():
    """Verify that inputs exceeding the 10,000 character maximum are rejected."""
    excessive_text = "A" * 10_001
    with pytest.raises(ValidationError):
        GenerateRequest(user_input=excessive_text)


def test_invalid_strategy_rejected():
    """Verify that unrecognized prompting strategy names are rejected by Pydantic."""
    with pytest.raises(ValidationError):
        GenerateRequest(user_input="Test", strategy="quantum_hyper_prompt")


def test_temperature_boundary_validation():
    """Verify that temperature below 0.0 or above 1.0 is rejected."""
    with pytest.raises(ValidationError):
        GenerateRequest(user_input="Test", temperature=-0.1)

    with pytest.raises(ValidationError):
        GenerateRequest(user_input="Test", temperature=1.5)

    # Valid boundaries
    req_min = GenerateRequest(user_input="Test", temperature=0.0)
    assert req_min.temperature == 0.0

    req_max = GenerateRequest(user_input="Test", temperature=1.0)
    assert req_max.temperature == 1.0


# ==============================================================================
# 2. Prompt Engineering Strategy & Delimiter Tests
# ==============================================================================

def test_zero_shot_prompt_construction():
    """Verify Zero-Shot prompt contains proper delimiters and does not contain few-shot examples."""
    prompt = build_zero_shot_prompt(
        user_input="Summarize gradient descent.",
        objective="Explain for beginners",
        constraints="Max 3 points",
        output_format="Markdown list"
    )

    assert "<user_input>" in prompt
    assert "</user_input>" in prompt
    assert "Summarize gradient descent." in prompt
    assert "<objective>" in prompt
    assert "<constraints>" in prompt
    assert "<output_format>" in prompt
    assert "<demonstrations>" not in prompt


def test_few_shot_prompt_construction():
    """Verify Few-Shot prompt includes representative demonstration exemplars."""
    prompt = build_few_shot_prompt(
        user_input="Classify: 'Super fast delivery, love it!'",
        role="Sentiment Classifier",
        objective="Categorize customer sentiment",
        constraints="Only return the category label",
        output_format="Text label"
    )

    assert "<demonstrations>" in prompt
    assert "</demonstrations>" in prompt
    assert "Example 1:" in prompt
    assert "Example 2:" in prompt
    assert "<user_input>" in prompt
    assert "Super fast delivery, love it!" in prompt


def test_role_prompt_construction():
    """Verify Role prompt establishes domain persona and context."""
    prompt = build_role_prompt(
        user_input="Explain distributed database consistency.",
        role="Principal Cloud Architect",
        context="System design interview candidate",
        constraints="Focus on PACELC theorem"
    )

    assert "<role>" in prompt
    assert "Principal Cloud Architect" in prompt
    assert "<context>" in prompt
    assert "System design interview candidate" in prompt
    assert "<constraints>" in prompt
    assert "PACELC theorem" in prompt
    assert "<user_input>" in prompt


def test_structured_prompt_construction():
    """Verify Structured prompt demands strict JSON and specifies the schema."""
    prompt = build_structured_prompt(
        user_input="Extract key concepts from prompt engineering.",
        role="Data Synthesizer"
    )

    assert "<output_format>" in prompt
    assert "Return ONLY a valid JSON object" in prompt
    assert '"summary"' in prompt
    assert '"key_points"' in prompt
    assert "<user_input>" in prompt


def test_expert_prompt_construction():
    """Verify Expert + Constraints synthesizes all 5 structural elements."""
    prompt = build_expert_prompt(
        user_input="Evaluate trade-offs between Monolith and Microservices.",
        role="Staff Infrastructure Architect",
        objective="Deliver architectural audit",
        context="Enterprise migration from monolith to cloud microservices",
        constraints="Cite bounded contexts and database per service",
        output_format="Four numbered sections"
    )

    assert "<role>" in prompt
    assert "<objective>" in prompt
    assert "<context>" in prompt
    assert "<constraints>" in prompt
    assert "<output_format>" in prompt
    assert "<user_input>" in prompt
    assert "Staff Infrastructure Architect" in prompt
    assert "bounded contexts" in prompt


def test_assemble_prompt_dispatcher():
    """Verify master assemble_prompt function returns system prompt and user prompt."""
    req = GenerateRequest(
        user_input="Analyze AI agent architectures.",
        strategy=PromptStrategy.EXPERT,
        role="Lead AI Engineer"
    )

    sys_prompt, usr_prompt = assemble_prompt(req)

    assert sys_prompt == SYSTEM_PROMPT
    assert "PromptLab AI" in sys_prompt
    assert "<role>" in usr_prompt
    assert "Lead AI Engineer" in usr_prompt
    assert "<user_input>" in usr_prompt


# ==============================================================================
# 3. JSON Output Validation Tests
# ==============================================================================

def test_json_validation_clean_valid():
    """Verify clean JSON string parses successfully."""
    raw = '{"summary": "Overview", "key_points": ["Point A", "Point B"], "examples": ["Ex 1"], "next_steps": ["Step 1"]}'
    valid, data, err = parse_and_validate_json_response(raw)

    assert valid is True
    assert err is None
    assert isinstance(data, dict)
    assert data["summary"] == "Overview"
    assert len(data["key_points"]) == 2


def test_json_validation_markdown_code_fences():
    """Verify parser extracts JSON wrapped in ```json ... ``` blocks."""
    raw = """```json
{
  "summary": "Extracted via code fence",
  "key_points": ["First point"],
  "examples": [],
  "next_steps": []
}
```"""
    valid, data, err = parse_and_validate_json_response(raw)

    assert valid is True
    assert err is None
    assert data["summary"] == "Extracted via code fence"


def test_json_validation_invalid_syntax():
    """Verify malformed JSON does not crash the server and returns clear error."""
    raw = '{"summary": "Broken JSON, missing closing quote, key_points: []'
    valid, data, err = parse_and_validate_json_response(raw)

    assert valid is False
    assert data is None
    assert err is not None
    assert "Invalid JSON" in err or "Failed to parse" in err


def test_json_validation_empty_string():
    """Verify empty string returns valid=False with helpful error."""
    valid, data, err = parse_and_validate_json_response("")
    assert valid is False
    assert data is None
    assert "empty" in err.lower()


# ==============================================================================
# 4. FastAPI Endpoints Integration Tests
# ==============================================================================

def test_endpoint_health():
    """Test /api/health endpoint returns expected schema."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "has_api_key" in data
    assert "default_model" in data
    assert "available_models" in data
    assert isinstance(data["available_models"], list)


def test_endpoint_strategies():
    """Test /api/strategies endpoint returns strategy descriptions."""
    response = client.get("/api/strategies")
    assert response.status_code == 200
    data = response.json()
    assert "strategies" in data
    assert len(data["strategies"]) == 5
    ids = [s["id"] for s in data["strategies"]]
    assert "zero_shot" in ids
    assert "few_shot" in ids
    assert "role" in ids
    assert "structured" in ids
    assert "expert" in ids


def test_endpoint_generate_validation_empty_input():
    """Test /api/generate rejects empty input with status 422 and clean error."""
    response = client.post("/api/generate", json={"user_input": "   "})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "error" in data


def test_endpoint_generate_graceful_missing_api_key():
    """
    Test /api/generate handles missing API key gracefully without crashing,
    returning structured response with explanation.
    """
    response = client.post(
        "/api/generate",
        json={
            "user_input": "Explain machine learning in 3 sentences.",
            "strategy": "zero_shot"
        }
    )
    # The server should respond 200 OK with success=False, or if API key is set, success=True
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "strategy" in data
    assert data["strategy"] == "zero_shot"
    assert "prompt_inspector" in data
    assert "system_prompt" in data["prompt_inspector"]
    assert "generated_prompt" in data["prompt_inspector"]
