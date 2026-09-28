<div align="center">

# 🧠 PromptLab AI

### *LLM Prompt Engineering & API Assistant*

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-V2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev)
[![Pytest](https://img.shields.io/badge/Pytest-18%20Tests-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br/>

[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=flat-square&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![Uvicorn](https://img.shields.io/badge/Uvicorn-ASGI-499848?style=flat-square&logo=gunicorn&logoColor=white)](https://www.uvicorn.org)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)](https://github.com/sunbyte16)
[![Day](https://img.shields.io/badge/Training-Day%201%20Applied%20AI%20Agents-6366F1?style=flat-square)](https://github.com/sunbyte16)

<br/>

> **A full-stack developer workbench to explore, test, inspect, and benchmark advanced LLM prompting strategies — with real API integrations and live side-by-side comparison.**

</div>

---

<div align="center">

## 📸 Application Showcase

</div>

<div align="center">

### 🖥️ Full Dashboard Overview
*Responsive dark-theme workspace — API health indicator, model controls, strategy cards, and prompt builder.*

![PromptLab AI Dashboard Overview](images/01_dashboard_overview.png)

</div>

---

<div align="center">

### 🧱 Prompt Builder & Strategy Selector
*5 prompting strategies, XML tag builder, real-time engineering checklist, and temperature slider.*

![Prompt Builder and Strategies](images/02_prompt_builder_and_strategies.png)

</div>

---

<div align="center">

### ✨ AI Response with Markdown & Latency Metrics
*Formatted AI output with status chips, model identifier, latency timer, token counts, and export actions.*

![AI Response with Markdown](images/04_ai_response_markdown.png)

</div>

---

<div align="center">

### 🔬 Deep Prompt Inspector
*Full transparency — exact system instructions and the XML-delimited prompt payload sent to the LLM.*

![Prompt Inspector](images/05_prompt_inspector.png)

</div>

---

<div align="center">

### 📦 Structured JSON Schema Output
*Schema-enforced generation with backend validation and a highlighted JSON tree with a `Validated` badge.*

![Structured JSON Output](images/06_structured_json_output.png)

</div>

---

<div align="center">

### ⚔️ Side-by-Side Strategy Comparison
*Compare two strategies on the same input — depth, tone, character count, and latency.*

![Strategy Comparison](images/07_strategy_comparison.png)

</div>

---

<div align="center">

### 📖 Prompt Engineering Principles Guide
*Embedded reference manual covering all six techniques with practical guidelines.*

![Prompt Techniques Guide](images/08_prompt_techniques_guide.png)

</div>

---

<div align="center">

### 🕓 Prompt History & Rapid Restore
*Browser-persisted history with timestamps, strategy tags, live filtering, and 1-click restore.*

![Prompt History](images/09_prompt_history.png)

</div>

---

## 📋 Table of Contents

| # | Section |
|---|---------|
| 1 | [✨ Overview](#-overview) |
| 2 | [🚀 Features](#-features) |
| 3 | [🏛️ Architecture](#️-architecture) |
| 4 | [🔧 Tech Stack](#-tech-stack) |
| 5 | [📁 Project Structure](#-project-structure) |
| 6 | [⚙️ Setup & Installation](#️-setup--installation) |
| 7 | [🔑 Environment Variables](#-environment-variables) |
| 8 | [▶️ Running the App](#️-running-the-app) |
| 9 | [🌐 API Reference](#-api-reference) |
| 10 | [🧪 Testing](#-testing) |
| 11 | [🛡️ Security](#️-security) |
| 12 | [🎓 Prompt Engineering Techniques](#-prompt-engineering-techniques) |
| 13 | [🎯 Demo Walkthrough](#-demo-walkthrough) |
| 14 | [🏆 Learning Outcomes](#-learning-outcomes) |

---

## ✨ Overview

Modern AI engineering demands **deliberate prompt architecture**, not just raw user text forwarded to a completion endpoint. **PromptLab AI** bridges that gap — it's a production-style educational workbench that teaches and demonstrates:

- 🧩 **Multi-strategy prompt construction** — Zero-Shot, Few-Shot, Role Prompting, Structured JSON, Expert + Constraints
- 🏷️ **XML delimiter compartmentalization** — `<role>` `<objective>` `<context>` `<constraints>` `<output_format>` `<user_input>`
- 🔒 **Safe step-by-step reasoning** without exposing private chain-of-thought tokens
- ✅ **Strict JSON schema enforcement** with automated backend validation
- ⚡ **Real-time side-by-side strategy comparison** with latency benchmarking
- 🔭 **Transparent prompt inspection** of every dispatched system and user message

---

## 🚀 Features

<details>
<summary><b>🧠 5 Prompting Strategies</b> — click to expand</summary>

<br/>

| Strategy | Description | Best For |
|----------|-------------|----------|
| ⚡ **Zero-Shot** | Direct task execution with explicit objectives and constraints | General Q&A, broad summaries, translations |
| 🎯 **Few-Shot** | Pattern conditioning via curated demonstration exemplar pairs | Classification, sentiment, custom formats |
| 🎭 **Role Prompting** | Persona alignment activating domain vocabulary and depth | Architecture reviews, code audits, expert analysis |
| 📦 **Structured Output** | Strict JSON schema compliance with backend validation | Data pipelines, API contracts, automated extractors |
| 🏆 **Expert + Constraints** | Full multi-variable composition with delimiter isolation | Enterprise tasks, multi-stakeholder analysis |

</details>

<details>
<summary><b>🔧 Interactive Visual Prompt Builder</b> — click to expand</summary>

<br/>

- Live fields for Persona (`<role>`), Goal (`<objective>`), Audience (`<context>`), Rules (`<constraints>`), and Format (`<output_format>`)
- Real-time **Prompt Quality Checklist** showing which engineering components are active
- Temperature slider `0.0 → 1.0` with behavioral guidance labels

</details>

<details>
<summary><b>⚔️ Side-by-Side Strategy Comparison</b> — click to expand</summary>

<br/>

- Execute two different strategies on the same input simultaneously
- Compare response quality, character count, and latency in a split view modal

</details>

<details>
<summary><b>🔬 Deep Prompt Inspector</b> — click to expand</summary>

<br/>

- View the exact **system instructions** dispatched to the model
- See the full **XML-delimited prompt payload** assembled at runtime

</details>

<details>
<summary><b>⚙️ Live Model Settings</b> — click to expand</summary>

<br/>

- Dynamic model selection: `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`, or any custom OpenAI-compatible endpoint
- Temperature slider with real-time guidance

</details>

<details>
<summary><b>📚 Prebuilt Examples & History</b> — click to expand</summary>

<br/>

- 1-click loading for Summarization, Classification, Technical Explanation, Data Science Comparison, and Structured 7-Day Plan
- Browser-persisted history with search, timestamps, and 1-click prompt restoration
- Export responses as `.txt` or validated `.json`

</details>

---

## 🏛️ Architecture

> A clean, decoupled three-tier architecture — **Frontend → FastAPI Backend → LLM Provider** — built for transparency, extensibility, and production-grade prompt engineering.

---

### 🗺️ System Architecture Overview

```mermaid
graph TB
    subgraph CLIENT["🌐  Browser Client  —  Presentation Layer"]
        direction LR
        UI["🖥️ index.html\nDashboard & Modals"]
        STYLE["🎨 style.css\nDark Theme · Animations"]
        APP["⚙️ app.js\nState · fetch API · MD Renderer\nJSON Formatter · LocalStorage"]
    end

    subgraph BACKEND["⚡  FastAPI Backend  —  Application Layer"]
        direction TB
        MAIN["🚦 main.py\nCORS · Routing · Error Normalization\nStatic File Hosting"]

        subgraph CORE["Core Modules"]
            direction LR
            PE["🧠 prompt_engine.py\nStrategy Builders\nXML Assembler\nJSON Validator"]
            LLM["🔌 llm_service.py\nOpenAI SDK Client\nLatency Timer\nToken Extractor"]
        end

        subgraph INFRA["Infrastructure"]
            direction LR
            MDL["📐 models.py\nPydantic V2 Schemas\nRequest · Response"]
            CFG["🔐 config.py\nEnv Vars · API Limits\nMasked Key"]
        end

        MAIN --> CORE
        MAIN --> INFRA
    end

    subgraph PROVIDERS["🤖  LLM Providers  —  Intelligence Layer"]
        direction LR
        OAI["OpenAI\ngpt-4o · gpt-4o-mini\ngpt-3.5-turbo"]
        GROQ["Groq\nFast Inference\nLlama · Mixtral"]
        OR["OpenRouter\nMulti-Model\nRouting"]
        OLLAMA["Ollama\nLocal Models\nPrivate Inference"]
    end

    CLIENT -- "HTTP REST\nJSON Payloads" --> BACKEND
    LLM -- "HTTPS · Bearer Token\nOpenAI-Compatible API" --> PROVIDERS

    style CLIENT fill:#1e293b,stroke:#6366f1,stroke-width:2px,color:#e2e8f0
    style BACKEND fill:#0f172a,stroke:#06b6d4,stroke-width:2px,color:#e2e8f0
    style CORE fill:#1e293b,stroke:#10b981,stroke-width:1px,color:#e2e8f0
    style INFRA fill:#1e293b,stroke:#f59e0b,stroke-width:1px,color:#e2e8f0
    style PROVIDERS fill:#1e293b,stroke:#8b5cf6,stroke-width:2px,color:#e2e8f0
```

---

### 🔄 Request Lifecycle

> End-to-end flow of a single `POST /api/generate` call — from browser click to rendered AI response.

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 User
    participant FE  as 🌐 Browser<br/>(app.js)
    participant API as ⚡ FastAPI<br/>(main.py)
    participant PE  as 🧠 Prompt Engine<br/>(prompt_engine.py)
    participant SVC as 🔌 LLM Service<br/>(llm_service.py)
    participant LLM as 🤖 LLM Provider<br/>(OpenAI / Groq / etc.)

    User->>FE: Clicks "Generate Response"
    FE->>FE: Validate input (client-side)
    FE->>API: POST /api/generate<br/>{ user_input, strategy, role, … }

    API->>API: Pydantic V2 schema validation
    API->>PE: assemble_prompt(request)

    PE->>PE: Select strategy builder<br/>(zero_shot / few_shot / role / structured / expert)
    PE->>PE: Inject XML delimiters<br/>⟨role⟩ ⟨objective⟩ ⟨context⟩ ⟨constraints⟩ ⟨output_format⟩ ⟨user_input⟩
    PE-->>API: (system_prompt, user_prompt)

    API->>SVC: generate_completion(messages, model, temperature)
    SVC->>SVC: Start latency timer ⏱️
    SVC->>LLM: HTTPS · chat.completions.create()
    LLM-->>SVC: Raw completion + token usage

    SVC->>SVC: Stop timer · extract usage metadata
    SVC-->>API: response_text, latency_ms, usage

    alt strategy == "structured"
        API->>PE: parse_and_validate_json(response_text)
        PE-->>API: (is_valid, parsed_dict, error_msg)
    end

    API-->>FE: GenerateResponse JSON<br/>{ success, response, strategy, latency_ms, usage, prompt_inspector }
    FE->>FE: Render Markdown / JSON tree
    FE-->>User: Formatted AI response + metrics
```

---

### 🧩 Component Diagram

> Internal composition of each layer — responsibilities, interfaces, and data contracts.

```mermaid
graph LR
    subgraph FE["🌐 Frontend Layer"]
        direction TB
        DASH["🖥️ Dashboard\nStrategy Cards\nModel Selector\nHealth Status"]
        BUILD["🔧 Prompt Builder\nRole · Objective\nContext · Constraints\nOutput Format\nQuality Checklist"]
        OUT["✨ Response Viewer\nMarkdown Renderer\nJSON Syntax Tree\nLatency · Token Chips\nCopy · Export"]
        INS["🔬 Prompt Inspector\nSystem Prompt View\nXML Payload View"]
        HIST["🕓 History Panel\nTimestamp · Tags\nSearch · Restore"]
        CMP["⚔️ Compare Modal\nDual Strategy\nSide-by-Side View"]
    end

    subgraph API["⚡ API Layer (FastAPI · Uvicorn)"]
        direction TB
        H["/api/health\nReadiness · Models\nMasked Key"]
        G["/api/generate\nPrimary Endpoint"]
        C["/api/compare\nDual Execution"]
        S["/api/strategies\nStrategy Metadata"]
        MW["🛡️ Middleware\nCORS · Validation\nError Normalizer"]
    end

    subgraph ENG["🧠 Prompt Engineering Layer"]
        direction TB
        ZS["⚡ Zero-Shot Builder\nbuild_zero_shot_prompt()"]
        FS["🎯 Few-Shot Builder\nbuild_few_shot_prompt()\n+ Demonstrations"]
        RP["🎭 Role Builder\nbuild_role_prompt()"]
        ST["📦 Structured Builder\nbuild_structured_prompt()\n+ JSON Schema"]
        EX["🏆 Expert Builder\nbuild_expert_prompt()\nFull Delimiter Suite"]
        AS["🔀 Assembler\nassemble_prompt()\ndispatch by strategy"]
        JV["✅ JSON Validator\nparse_and_validate_json()\nFence Stripping · Recovery"]
    end

    subgraph SVC["🔌 LLM Service Layer"]
        direction TB
        GC["generate_completion()\nSingle Strategy Call"]
        CS["compare_strategies()\nParallel Dual Call"]
        SDK["OpenAI SDK Client\nchat.completions.create()"]
        LT["⏱️ Latency Timer\ntime.perf_counter()"]
        EM["🛑 Error Mapper\nHTTPException\nFriendly Messages"]
    end

    subgraph PROV["🤖 LLM Providers"]
        direction LR
        P1["OpenAI\napi.openai.com"]
        P2["Groq\napi.groq.com"]
        P3["OpenRouter\nopenrouter.ai"]
        P4["Ollama\nlocalhost:11434"]
    end

    FE -- "HTTP fetch()\nJSON" --> API
    API --> ENG
    API --> SVC
    ENG --> AS
    AS --> ZS & FS & RP & ST & EX
    SVC --> GC & CS
    GC & CS --> SDK
    SDK -- "HTTPS" --> PROV

    style FE fill:#1e293b,stroke:#6366f1,color:#e2e8f0
    style API fill:#0f172a,stroke:#06b6d4,color:#e2e8f0
    style ENG fill:#1e293b,stroke:#10b981,color:#e2e8f0
    style SVC fill:#0f172a,stroke:#f59e0b,color:#e2e8f0
    style PROV fill:#1e293b,stroke:#8b5cf6,color:#e2e8f0
```

---

### 📊 Prompt Strategy Decision Flow

> How the engine selects and assembles the correct prompt for every request.

```mermaid
flowchart TD
    A(["📥 POST /api/generate\nIncoming Request"]) --> B["🛡️ Pydantic V2\nSchema Validation"]
    B -- "❌ Invalid" --> ERR["422 Validation Error\nFriendly Message → Client"]
    B -- "✅ Valid" --> C{"🔀 Strategy\nRouter"}

    C -- "zero_shot" --> D["⚡ Zero-Shot Builder\n&lt;objective&gt; &lt;constraints&gt;\n&lt;output_format&gt; &lt;user_input&gt;"]
    C -- "few_shot"  --> E["🎯 Few-Shot Builder\n&lt;demonstrations&gt;\n3 Exemplar Pairs\n&lt;user_input&gt;"]
    C -- "role"      --> F["🎭 Role Builder\n&lt;role&gt; &lt;context&gt;\n&lt;objective&gt; &lt;constraints&gt;\n&lt;user_input&gt;"]
    C -- "structured"--> G["📦 Structured Builder\n&lt;output_format&gt;\nJSON Schema Enforced\n&lt;user_input&gt;"]
    C -- "expert"    --> H["🏆 Expert Builder\nFull Delimiter Suite\n&lt;role&gt; &lt;objective&gt; &lt;context&gt;\n&lt;constraints&gt; &lt;output_format&gt;\n&lt;user_input&gt;"]

    D & E & F & G & H --> I["📦 Assembled Prompt Payload\nSystem Prompt + User Prompt"]
    I --> J["🔌 LLM Service\nOpenAI SDK · Latency Timer"]
    J --> K["🤖 LLM Provider\nchat.completions.create()"]
    K --> L{"📦 Strategy\n== structured?"}

    L -- "Yes" --> M["✅ JSON Validator\nFence Strip · Parse · Schema Check"]
    M -- "Valid JSON" --> N["✅ structured: true\nparsed_json: {...}"]
    M -- "Parse Error" --> O["⚠️ structured: false\nvalidation_error: ..."]
    L -- "No"  --> P["📝 Markdown Response\nstructured: false"]

    N & O & P --> Q["📤 GenerateResponse\n{ success · response · latency_ms\nusage · prompt_inspector }"]
    Q --> R(["🌐 Browser Client\nRender Markdown / JSON Tree"])

    style A fill:#6366f1,color:#fff,stroke:none
    style R fill:#10b981,color:#fff,stroke:none
    style ERR fill:#ef4444,color:#fff,stroke:none
    style C fill:#0f172a,stroke:#06b6d4,color:#e2e8f0
    style L fill:#0f172a,stroke:#f59e0b,color:#e2e8f0
    style I fill:#1e293b,stroke:#10b981,color:#e2e8f0
    style Q fill:#1e293b,stroke:#8b5cf6,color:#e2e8f0
```

---

## 🔧 Tech Stack

<div align="center">

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| 🐍 Backend Runtime | Python | 3.12 | Core application language |
| ⚡ API Framework | FastAPI | ≥ 0.110 | REST endpoints, routing, middleware |
| 🚀 ASGI Server | Uvicorn | ≥ 0.28 | High-performance async server |
| ✅ Data Validation | Pydantic V2 | ≥ 2.6 | Request/response schema enforcement |
| 🤖 LLM Integration | OpenAI SDK | ≥ 1.14 | GPT model API calls |
| 🔐 Config Mgmt | python-dotenv | ≥ 1.0.1 | Secure environment variable loading |
| 🧪 Testing | Pytest + HTTPX | ≥ 8.0 | 18 automated tests |
| 🌐 Frontend | HTML5 + CSS3 + JS ES6+ | — | Dark-theme responsive dashboard |

</div>

---

## 📁 Project Structure

```
📦 Day 1 LLM Fundamentals & Prompt Engineering/
│
├── 🐍 backend/
│   ├── __init__.py           # Package marker
│   ├── config.py             # Env vars, security limits, masked key
│   ├── models.py             # Pydantic request/response schemas
│   ├── prompt_engine.py      # Prompt builders, delimiters, JSON validator
│   ├── llm_service.py        # OpenAI client, latency timing, error handlers
│   └── main.py               # FastAPI routes, CORS, static hosting
│
├── 🌐 frontend/
│   ├── index.html            # Developer dashboard layout & modals
│   ├── style.css             # Dark theme, animations, responsive grid
│   └── app.js                # State management, API calls, MD/JSON rendering
│
├── 🖼️ images/                # UI screenshots & showcase assets
│   ├── 01_dashboard_overview.png
│   ├── 02_prompt_builder_and_strategies.png
│   ├── 03_user_input_and_examples.png
│   ├── 04_ai_response_markdown.png
│   ├── 05_prompt_inspector.png
│   ├── 06_structured_json_output.png
│   ├── 07_strategy_comparison.png
│   ├── 08_prompt_techniques_guide.png
│   ├── 09_prompt_history.png
│   └── 10_full_application_showcase.png
│
├── 🧪 tests/
│   ├── __init__.py           # Test package marker
│   └── test_prompt_engine.py # 18 unit + integration tests
│
├── 📄 .env.example           # Environment variables template
├── 🚫 .gitignore             # Git ignore (.env, .venv, caches)
├── 📋 requirements.txt       # Python dependencies
└── 📖 README.md              # This file
```

---

## ⚙️ Setup & Installation

### 📋 Prerequisites

- ✅ Python 3.10+
- ✅ An OpenAI API Key (or compatible provider key)
- ✅ Git

---

### Step 1 — Clone or Navigate to the Project

```powershell
cd "Day 1 LLM Fundamentals & Prompt Engineering"
```

### Step 2 — Create & Activate Virtual Environment

**🪟 Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**🍎 macOS / 🐧 Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3 — Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Copy the template and configure your API key:

**🪟 Windows:**
```powershell
Copy-Item .env.example .env
```

**🍎 macOS / 🐧 Linux:**
```bash
cp .env.example .env
```

Edit `.env`:
```env
# 🔑 Primary LLM API Key (OpenAI or compatible provider)
OPENAI_API_KEY=sk-your-actual-api-key-here

# 🌐 Optional: Custom API Base URL for OpenAI-compatible providers
# OpenAI Official: https://api.openai.com/v1         (default)
# Groq:           https://api.groq.com/openai/v1
# OpenRouter:     https://openrouter.ai/api/v1
# Ollama (Local): http://localhost:11434/v1
OPENAI_BASE_URL=

# 🤖 Default Model
DEFAULT_MODEL=gpt-4o-mini

# 🖥️ Server Configuration
HOST=127.0.0.1
PORT=8000
```

> 💡 **No API Key yet?** The backend starts gracefully and notifies you through the UI health indicator. The **Prompt Inspector** remains fully functional — you can explore all prompt engineering mechanics immediately without spending any API credits.

---

## ▶️ Running the App

```powershell
.venv\Scripts\uvicorn backend.main:app --reload --port 8000
```

Then open your browser:

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000/` | 🖥️ Main Dashboard |
| `http://127.0.0.1:8000/docs` | 📘 Interactive Swagger API Docs |
| `http://127.0.0.1:8000/redoc` | 📗 ReDoc API Documentation |

---

## 🌐 API Reference

### `GET /api/health`
> Returns application readiness, API key status, and available models.

```json
{
  "status": "ready",
  "has_api_key": true,
  "default_model": "gpt-4o-mini",
  "available_models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
  "masked_key": "sk-****1234"
}
```

---

### `POST /api/generate`
> Applies a prompt engineering strategy and calls the LLM.

**Request:**
```json
{
  "user_input": "Explain backpropagation in deep neural networks.",
  "strategy": "role",
  "role": "Distinguished Professor of AI",
  "objective": "Explain gradient updates for undergraduates",
  "context": "CS students learning calculus and linear algebra",
  "constraints": "Keep under 300 words. Highlight intuition first.",
  "output_format": "Markdown with bullet points",
  "model": "gpt-4o-mini",
  "temperature": 0.3
}
```

**Response:**
```json
{
  "success": true,
  "response": "### Core Intuition...",
  "strategy": "role",
  "model": "gpt-4o-mini",
  "structured": false,
  "prompt_inspector": {
    "system_prompt": "You are PromptLab AI...",
    "generated_prompt": "<role>Distinguished Professor of AI</role>...",
    "strategy": "role"
  },
  "usage": {
    "prompt_tokens": 142,
    "completion_tokens": 210,
    "total_tokens": 352
  },
  "latency_ms": 1120.45
}
```

---

### `POST /api/compare`
> Executes two strategies side-by-side for identical input.

### `GET /api/strategies`
> Returns descriptions and metadata for all 5 prompting strategies.

---

## 🎓 Prompt Engineering Techniques

| 🏷️ Technique | 📝 Description | 🔖 Delimiters | ✅ Ideal Use Cases |
|:---|:---|:---|:---|
| ⚡ **Zero-Shot** | Direct instruction, no examples | `<objective>` `<constraints>` `<output_format>` `<user_input>` | General Q&A, broad summaries, translation |
| 🎯 **Few-Shot** | In-context exemplar pairs demonstrating desired pattern | `<demonstrations>` `<user_input>` | Sentiment, classification, domain-specific formatting |
| 🎭 **Role Prompting** | Explicit professional persona | `<role>` `<context>` `<objective>` `<constraints>` | Architecture reviews, code audits, expert analysis |
| 📦 **Structured Output** | Strict JSON schema adherence | `<output_format>` (JSON Schema) | Data pipelines, API contracts, extractors |
| 🏆 **Expert + Constraints** | Full multi-variable composition | All tags combined | Enterprise tasks, policy adherence, stakeholder analysis |
| 🔗 **Safe Chain-of-Thought** | Structured reasoning steps, no hidden token exposure | Explicit constraint in `<constraints>` | Math reasoning, trade-off analysis, debugging |

---

## 🧪 Testing

PromptLab AI includes **18 automated tests** covering input validation, delimiter assembly, JSON recovery, and FastAPI endpoints.

```powershell
.venv\Scripts\pytest -v
```

**Expected output:**
```
============================= test session starts ==============================
collected 18 items

tests/test_prompt_engine.py::test_empty_user_input_rejected          PASSED ✓
tests/test_prompt_engine.py::test_excessive_user_input_rejected       PASSED ✓
tests/test_prompt_engine.py::test_invalid_strategy_rejected           PASSED ✓
tests/test_prompt_engine.py::test_temperature_boundary_validation     PASSED ✓
tests/test_prompt_engine.py::test_zero_shot_prompt_construction       PASSED ✓
tests/test_prompt_engine.py::test_few_shot_prompt_construction        PASSED ✓
tests/test_prompt_engine.py::test_role_prompt_construction            PASSED ✓
tests/test_prompt_engine.py::test_structured_prompt_construction      PASSED ✓
tests/test_prompt_engine.py::test_expert_prompt_construction          PASSED ✓
tests/test_prompt_engine.py::test_assemble_prompt_dispatcher          PASSED ✓
tests/test_prompt_engine.py::test_json_validation_clean_valid         PASSED ✓
tests/test_prompt_engine.py::test_json_validation_markdown_fences     PASSED ✓
tests/test_prompt_engine.py::test_json_validation_invalid_syntax      PASSED ✓
tests/test_prompt_engine.py::test_json_validation_empty_string        PASSED ✓
tests/test_prompt_engine.py::test_endpoint_health                     PASSED ✓
tests/test_prompt_engine.py::test_endpoint_strategies                 PASSED ✓
tests/test_prompt_engine.py::test_endpoint_generate_validation        PASSED ✓
tests/test_prompt_engine.py::test_endpoint_graceful_missing_api_key   PASSED ✓

========================= 18 passed in 4.24s ==================================
```

---

## 🛡️ Security

| # | Practice | Implementation |
|---|----------|----------------|
| 🔑 | **Server-Side API Key** | Key stored in `.env`, loaded by `config.py` — never in client HTML/JS |
| 👁️ | **Masked Key Display** | Diagnostics show only `sk-****1234` — never the full key |
| 🚫 | **Git Hygiene** | `.gitignore` prevents `.env`, `.venv`, and `__pycache__` from commits |
| 🧹 | **Input Sanitization** | Pydantic rejects empty strings, whitespace-only inputs, and requests > 10,000 chars |
| 🌡️ | **Temperature Bounds** | Constrained to `[0.0, 1.0]` via Pydantic field validation |
| 🛑 | **Error Normalization** | Stack traces and credentials intercepted server-side; clean messages returned to client |

---

## 🎯 Demo Walkthrough

Follow these steps for a guided evaluation of PromptLab AI:

```
1. 🚀 Launch       →  uvicorn backend.main:app --reload  →  open localhost:8000
2. 🏥 Health Check →  Observe the API status indicator in the header
3. ⚡ Zero-Shot    →  Load "Summarization" example  →  Generate Response
4. 🔬 Inspect      →  Switch to Prompt Inspector tab  →  View XML-delimited payload
5. 🎯 Few-Shot     →  Load "Classification" example  →  Note strategy auto-switch
6. 📦 Structured   →  Load "Structured Plan"  →  Observe validated JSON tree
7. ⚔️ Compare      →  Click Compare Strategies  →  Zero-Shot vs Role Prompting
8. ❌ Error Test   →  Clear input  →  Submit  →  Observe friendly validation message
9. 📤 Export       →  Export response as .json or .txt
10. 🕓 History     →  Open Prompt History  →  Filter and 1-click restore
```

---

## 🏆 Learning Outcomes

- ✅ **LLM API Fundamentals** — Client initialization, authentication, parameter tuning, and response parsing
- ✅ **Advanced Prompt Engineering** — Zero-Shot, Few-Shot exemplars, Role conditioning, XML delimiter isolation, Structured JSON output
- ✅ **Enterprise Software Principles** — Clean separation of concerns across config, prompt engine, service gateway, data validation, and frontend
- ✅ **Production Security Patterns** — Server-side key management, input validation, masked diagnostics, safe error normalization
- ✅ **Automated Testing** — Pydantic validation tests, endpoint integration tests, JSON recovery tests

---

<div align="center">

## 📊 Full Application Showcase

![Full Application Showcase](images/10_full_application_showcase.png)

</div>

---

<div align="center">

## 👨‍💻 Created By

<br/>

### 𝕊𝕦𝕟𝕚𝕝 𝕊𝕙𝕒𝕣𝕞𝕒 ❤️

*Built with passion for AI, clean code, and continuous learning.*

<br/>

[![GitHub](https://img.shields.io/badge/GitHub-sunbyte16-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sunbyte16)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Sunil%20Kumar-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/sunil-kumar-bb88bb31a/)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit%20Site-FF6B6B?style=for-the-badge&logo=netlify&logoColor=white)](https://lively-dodol-cc397c.netlify.app)

<br/>

---

*⭐ If you found this useful, consider starring the repository!*

</div>
