"""
PromptLab AI - Main FastAPI Application
Serves API endpoints for prompt generation, strategy comparison, health check,
and static frontend dashboard assets.
"""

import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend import config
from backend.models import (
    GenerateRequest,
    GenerateResponse,
    CompareRequest,
    CompareResponse,
    HealthResponse,
)
from backend.llm_service import generate_completion, compare_strategies

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("promptlab.main")

# Initialize FastAPI application
app = FastAPI(
    title="PromptLab AI",
    description="LLM Prompt Engineering & API Assistant - Day 1 Applied AI Agents",
    version="1.0.0"
)

# Enable CORS for local development and testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom validation exception handler to return friendly user-facing messages
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    field = " -> ".join(str(loc) for loc in first_error.get("loc", []))
    msg = first_error.get("msg", "Invalid request parameters.")

    clean_message = f"Validation Error on '{field}': {msg}"
    logger.warning(f"Request validation failed: {clean_message}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "success": False,
            "error": clean_message,
            "response": clean_message,
            "details": [
                {"field": " -> ".join(str(l) for l in err.get("loc", [])), "message": err.get("msg")}
                for err in errors
            ]
        }
    )


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Returns application health, API key presence status, and available models."""
    has_key = config.is_api_key_configured()
    status_str = "ready" if has_key else "api_key_missing"

    return HealthResponse(
        status=status_str,
        has_api_key=has_key,
        default_model=config.DEFAULT_MODEL,
        available_models=config.AVAILABLE_MODELS,
        masked_key=config.get_masked_api_key()
    )


@app.get("/api/strategies")
async def get_prompting_strategies():
    """Returns educational descriptions of each supported prompting strategy."""
    return {
        "strategies": [
            {
                "id": "zero_shot",
                "name": "Zero-Shot Prompting",
                "tagline": "Direct instruction without in-context examples",
                "description": "Instructs the LLM directly on what to accomplish. Highly effective for general reasoning, zero-overhead queries, and models with strong pre-trained knowledge.",
                "best_for": "Straightforward tasks, broad questions, general summarization."
            },
            {
                "id": "few_shot",
                "name": "Few-Shot Prompting",
                "tagline": "Pattern learning via demonstration input-output pairs",
                "description": "Conditions the LLM by providing several exemplary (Input -> Reasoning -> Output) demonstrations before presenting the real task to steer format, tone, and depth.",
                "best_for": "Classification, sentiment analysis, custom extraction formats."
            },
            {
                "id": "role",
                "name": "Role Prompting",
                "tagline": "Persona, domain expertise, and tone steering",
                "description": "Assigns a specific professional identity (e.g. Senior ML Engineer, Security Auditor) to prime the model's vocabulary, rigor, and technical nuance.",
                "best_for": "Domain-specific analysis, technical design, audience-tailored answers."
            },
            {
                "id": "structured",
                "name": "Structured Output",
                "tagline": "Strict JSON schema enforcement and validation",
                "description": "Enforces a machine-readable JSON structure with validated schema fields (summary, key_points, examples, next_steps) ready for downstream software consumption.",
                "best_for": "Data pipelines, API-to-API communication, structured summaries."
            },
            {
                "id": "expert",
                "name": "Expert + Constraints",
                "tagline": "Full delimiter isolation (<role>, <objective>, <context>, etc.)",
                "description": "Combines role persona, clear objective, context, strict negative/positive constraints, and precise output format using XML delimiters for maximum fidelity and steerability.",
                "best_for": "Complex enterprise tasks, high-stakes analysis, policy adherence."
            }
        ]
    }


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Primary endpoint: Takes user input, applies prompt engineering strategy,
    calls LLM API, and returns structured response and prompt inspector metadata.
    """
    try:
        response = generate_completion(request)
        return response
    except Exception as e:
        logger.exception("Unexpected error in /api/generate endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to contact the LLM service. Please check your API configuration and try again."
        )


@app.post("/api/compare", response_model=CompareResponse)
async def compare(request: CompareRequest):
    """
    Comparison endpoint: Executes two distinct prompting strategies side-by-side
    for identical input, returning both responses with execution metrics.
    """
    try:
        return compare_strategies(request)
    except Exception as e:
        logger.exception("Unexpected error in /api/compare endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to execute strategy comparison. Please check your API configuration and try again."
        )


# ==============================================================================
# Static Files & Frontend Dashboard Mounting
# ==============================================================================
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    # Mount frontend directory for css, js, icons, etc.
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        """Serves the primary developer dashboard index.html."""
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse({"message": "PromptLab AI API running. Frontend index.html not found."})
