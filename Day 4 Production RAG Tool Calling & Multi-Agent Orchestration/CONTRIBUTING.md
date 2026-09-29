<div align="center">

# 🤝 Contributing to OrchestraRAG AI

**Production Multi-Agent RAG, Safe Tool Calling & Dynamic Graph Orchestration Platform**

Thank you for your interest in contributing to **OrchestraRAG AI**! Whether you are fixing bugs, adding new specialized agents, implementing safe tool sandboxes, improving retrieval benchmarks, or refining the dashboard, your contributions are welcome and greatly appreciated.

[![GitHub](https://img.shields.io/badge/GitHub-sunbyte16-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sunbyte16)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome_🤝-blueviolet?style=for-the-badge)](https://github.com/sunbyte16)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph_0.2.60-orange?style=for-the-badge)](https://github.com/langchain-ai/langgraph)
[![Tests Passing](https://img.shields.io/badge/Tests-30%2F30_Passed-success?style=for-the-badge)](./tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](./LICENSE)

</div>

---

## 📋 Table of Contents

1. [Code of Conduct](#-code-of-conduct)
2. [How Can I Contribute?](#-how-can-i-contribute)
3. [Local Development Setup](#-local-development-setup)
4. [Project Architecture & Directory Layout](#-project-architecture--directory-layout)
5. [Core Architectural Guardrails](#-core-architectural-guardrails)
6. [Coding Standards & Conventions](#-coding-standards--conventions)
7. [Running Tests & Evaluation Benchmarks](#-running-tests--evaluation-benchmarks)
8. [Commit Message Guidelines](#-commit-message-guidelines)
9. [Pull Request Process](#-pull-request-process)
10. [Roadmap & High-Priority Areas](#-roadmap--high-priority-areas)

---

## 🌟 Code of Conduct

This project is dedicated to providing an inclusive, harassment-free, and welcoming experience for everyone.

### Principles:
* **Respectful Collaboration**: Treat all contributors with empathy, respect, and constructive professionalism.
* **Objective Code Reviews**: Critique ideas and implementations constructively, not individuals.
* **Documentation & Attribution**: Always credit original authors and document rationale for architectural decisions.
* **Safety First**: Do not submit pull requests that introduce insecure execution mechanisms (e.g., Python `eval()`, unparameterized SQL execution, or unsanitized prompt injection vectors).

---

## 🧰 How Can I Contribute?

There are many ways to make an impact:

| Contribution Area | Examples & Opportunities |
|---|---|
| 🤖 **New Specialized Agents** | Implement a `CodeAgent`, `SummarizationAgent`, or `DataAnalysisAgent` within the LangGraph state machine. |
| 🛡️ **Tool Sandboxing** | Add safe, sandboxed tools (e.g., sandboxed Python WASM execution, Docker executor, WolframAlpha API). |
| 📚 **RAG & Vector Stores** | Add adapters for Qdrant, Pinecone, Milvus, or Weaviate; build BM25 + dense hybrid search with reciprocal rank fusion (RRF). |
| 🔍 **Contradiction Detection** | Refine NLI (Natural Language Inference) cross-document contradiction heuristics in the `VerificationAgent`. |
| 📊 **Observability Exporters** | Add OpenTelemetry (OTel), Prometheus, or LangSmith trace streaming. |
| 🎨 **Frontend Enhancements** | Enhance the interactive SVG graph visualizer, add real-time WebSocket token streaming, or improve responsive layouts. |
| 🧪 **Test Coverage** | Add unit tests for edge cases, adversarial prompt injection payloads, or malformed queries. |
| 📖 **Documentation** | Improve system architecture diagrams, expand API guides, or document setup for different operating systems. |

---

## 🛠️ Local Development Setup

### 1. Prerequisites
* **Python**: 3.10, 3.11, or 3.12 installed.
* **Git**: Installed and configured.
* **API Key**: A free Groq API key from [console.groq.com](https://console.groq.com) (or an OpenAI API key).

### 2. Fork and Clone the Repository
```bash
# Clone your fork
git clone https://github.com/<your-username>/Applied-AI-Agents-Projects.git
cd "Applied-AI-Agents-Projects/Day 4 Production RAG Tool Calling & Multi-Agent Orchestration"
```

### 3. Create a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy the template configuration file:
```bash
cp .env.example .env
```
Edit `.env` to supply your API credentials:
```ini
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
HOST=127.0.0.1
PORT=8000
```

### 6. Verify Local Installation
Start the unified application server:
```bash
python -m backend.main
```
Open your browser to [http://127.0.0.1:8000](http://127.0.0.1:8000) and verify that the system health indicator shows `Operational`.

---

## 📂 Project Architecture & Directory Layout

```text
.
├── backend/
│   ├── agents/            # 6 Specialized Autonomous Agents
│   │   ├── orchestrator.py        # Intent planning & dynamic graph routing
│   │   ├── rag_agent.py           # Vector retrieval & chunk filtering
│   │   ├── research_agent.py      # Live external web search (DDGS)
│   │   ├── tool_agent.py          # Sandboxed tool execution & result extraction
│   │   ├── synthesis_agent.py     # Grounded evidence synthesis with citations
│   │   └── verification_agent.py  # Grounding audit & contradiction surfacing
│   ├── evaluation/        # Automated 7-case benchmark runner
│   │   └── evaluator.py
│   ├── observability/     # Execution tracer, latency metrics, span capture
│   │   └── tracer.py
│   ├── orchestration/     # LangGraph StateGraph & SharedWorkflowState
│   │   ├── graph.py
│   │   └── state.py
│   ├── rag/               # Document parsing, chunking, embeddings, ChromaDB
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   ├── parser.py
│   │   └── vector_store.py
│   ├── tools/             # Sandboxed tools & registry
│   │   ├── base.py
│   │   ├── calculator.py          # AST-only safe arithmetic evaluator
│   │   ├── custom_analytics.py    # Statistical & percentage improvement tool
│   │   ├── database_tool.py       # Read-only SQLite query tool
│   │   ├── registry.py
│   │   ├── search_tool.py
│   │   └── weather_tool.py
│   ├── config.py          # Centralized configuration & guardrail thresholds
│   ├── llm.py             # Unified LLM provider abstraction (Groq / OpenAI)
│   ├── main.py            # FastAPI REST application & static frontend server
│   └── models.py          # Pydantic schemas (Evidence, ToolCall, TraceEvent)
├── data/
│   └── app_database.sqlite# Read-only SQLite enterprise database
├── evaluation/
│   ├── evaluation_report.json     # Empirical evaluation results
│   └── test_cases.json    # 7 standardized benchmark evaluation scenarios
├── frontend/              # Enterprise web dashboard
│   ├── app.js             # UI coordination, SVG graph animator, timeline stream
│   ├── index.html         # Simple and Advanced dual-mode dashboard
│   └── styles.css         # Dark theme glassmorphic styling
├── images/                # Visual documentation screenshots & figures
├── sample_docs/           # Seed knowledge base documents
├── tests/                 # Automated pytest test suite (30 tests)
├── .env.example           # Environment template
├── CONTRIBUTING.md        # Contribution guidelines (this file)
├── LICENSE                # MIT License
├── README.md              # 22-section comprehensive documentation
└── requirements.txt       # Pinned dependencies
```

---

## 🔒 Core Architectural Guardrails

When contributing code, you **MUST** adhere to the following safety and structural invariants:

### 1. Absolute Prohibition of `eval()` / `exec()`
Under no circumstances should user input or LLM generated code be evaluated with Python's built-in `eval()`, `exec()`, or `compile()`.
* All mathematical calculations must parse syntax trees via `ast.parse` and whitelist only safe numerical nodes (`ast.BinOp`, `ast.Constant`, `ast.Add`, etc.).

### 2. Read-Only Database Security
Any database tools must enforce read-only semantics:
* Reject any query containing mutating tokens (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `EXEC`).
* Detect and block statement stacking (semicolon separators).
* Always bind parameters and enforce result limits (`LIMIT 50`).

### 3. Untrusted Context Boundaries for Prompt Injection Defense
All retrieved document text and web search snippets provided to LLMs must be isolated inside explicit XML boundary wrappers:
```text
<untrusted_retrieved_context provenance="document.pdf" chunk_id="chunk_1">
{retrieved_chunk_content}
</untrusted_retrieved_context>
```
System prompts must instruct models never to interpret text within these boundary tags as instructions or system overrides.

### 4. LangGraph Node-Key Decoupling & Loop Limits
* **Naming Collision**: In LangGraph, node function names cannot match state schema keys. Always suffix graph nodes (e.g., `orchestrator_agent`, `verification_agent`) to decouple them from state attributes (`plan`, `verification`).
* **Deterministic Loop Bounds**: Verification loops must increment `verification_loop_count` within graph nodes and enforce `MAX_VERIFICATION_LOOPS = 2` to prevent infinite cycle traps.

---

## 📐 Coding Standards & Conventions

* **PEP 8**: Follow standard Python style guidelines.
* **Type Annotations**: All function signatures, agent handlers, and tool inputs/outputs must be strictly typed using standard Python type hints and `pydantic` models.
* **Docstrings**: Include descriptive Google-style or Sphinx-style docstrings explaining the purpose, arguments, and return values.
* **Pydantic Validation**: All API request and response payloads must use Pydantic models defined in [`backend/models.py`](file:///c:/Users/sharm/OneDrive/Desktop/Training%20Program/Applied%20AI%20Agents/Day%204%20Production%20RAG%20Tool%20Calling%20&%20Multi-Agent%20Orchestration/backend/models.py).
* **Async Handlers**: Use `async/await` for I/O-bound operations (FastAPI endpoints, HTTP requests, LLM API calls).

---

## 🧪 Running Tests & Evaluation Benchmarks

Before opening a pull request, verify that your changes pass all unit tests and evaluation benchmarks.

### 1. Run the Complete Pytest Suite
```bash
pytest -v
```
Ensure all 30 tests pass with **100% success rate**:
* `tests/test_agents.py`: Unit tests for specialized agents and intent routing.
* `tests/test_rag.py`: Document parsing, recursive chunking, dense embeddings, and ChromaDB retrieval.
* `tests/test_tools.py`: Safe AST calculator, read-only SQL, Open-Meteo weather, and analytics tools.
* `tests/test_workflow.py`: End-to-end multi-agent LangGraph workflow execution.
* `tests/test_security.py`: Prompt injection isolation, AST injection rejection, and loop boundary checks.

### 2. Run the Automated 7-Scenario Evaluation Benchmark
```bash
python -m backend.evaluation.evaluator
```
This runs the full benchmark across tool calling, RAG retrieval, multi-agent collaboration, hallucination control, contradiction detection, and prompt injection defense, updating `evaluation/evaluation_report.json`.

---

## 💬 Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```text
<type>(<scope>): <short description>

[optional body explaining rationale]

[optional footer(s)]
```

### Commit Types:
* `feat`: A new feature or agent capability (e.g., `feat(agents): add code interpreter agent`)
* `fix`: A bug fix (e.g., `fix(rag): handle empty retrieval results gracefully`)
* `docs`: Documentation updates or additions (e.g., `docs(readme): add sequence diagram`)
* `test`: Adding or updating test cases (e.g., `test(security): add prompt injection regression test`)
* `refactor`: Code refactoring that does not change external behavior
* `perf`: Performance optimizations (e.g., `perf(embeddings): batch chunk vectorization`)

---

## 🚀 Pull Request Process

1. **Branch Naming**: Create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. **Implement & Test**: Write clean, typed code and add relevant tests in `tests/`.
3. **Run Validation**: Ensure `pytest -v` passes completely.
4. **Update Documentation**: Update `README.md` or docstrings if your change introduces new tools, endpoints, or environment variables.
5. **Open Pull Request**: Submit the PR against the `main` branch with:
   - A clear description of the problem solved.
   - An overview of the architectural changes made.
   - Screenshots or terminal logs verifying test and evaluation passes.

---

## 🗺️ Roadmap & High-Priority Areas

Interested in contributing but not sure where to start? Check out these high-priority roadmap initiatives:

1. **Streaming Token Delivery**: Implement WebSockets or Server-Sent Events (SSE) to stream partial tokens and real-time node state transitions to the web dashboard.
2. **Hybrid Retrieval (BM25 + Dense Vectors)**: Integrate sparse BM25 indexing alongside ChromaDB dense vectors using Reciprocal Rank Fusion (RRF).
3. **Document Ingestion OCR**: Add Tesseract OCR support to `DocumentParser` for scanned PDFs and image diagrams.
4. **Persistent Multi-Session Memory**: Implement Redis-backed conversation checkpoints for LangGraph state persistence across browser reloads.
5. **OpenTelemetry Trace Export**: Add an OTel exporter in `backend/observability/tracer.py` to stream spans directly to Jaeger, Prometheus, or Datadog.

---

## 📬 Questions or Feedback?

Have questions or need assistance getting started?
* Open a [GitHub Issue](https://github.com/sunbyte16/Applied-AI-Agents-Projects/issues).
* Explore the [Interactive Swagger Documentation](http://127.0.0.1:8000/docs) when running the server locally.

Thank you for helping build **OrchestraRAG AI**! 🚀
