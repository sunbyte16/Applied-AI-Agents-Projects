<div align="center">

# 🤝 Contributing to DocuRAG AI

**Thank you for taking the time to contribute!**
Every improvement — big or small — makes DocuRAG AI better for everyone.

[![GitHub](https://img.shields.io/badge/GitHub-sunbyte16-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sunbyte16)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome_🤝-blueviolet?style=for-the-badge)](https://github.com/sunbyte16)
[![Code of Conduct](https://img.shields.io/badge/Code_of_Conduct-✅_Enforced-green?style=for-the-badge)]()

</div>

---

## 📋 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [How Can I Contribute?](#-how-can-i-contribute)
- [Development Setup](#-development-setup)
- [Project Structure](#-project-structure)
- [Coding Standards](#-coding-standards)
- [Commit Message Guidelines](#-commit-message-guidelines)
- [Pull Request Process](#-pull-request-process)
- [Reporting Bugs](#-reporting-bugs)
- [Suggesting Features](#-suggesting-features)
- [Areas That Need Help](#-areas-that-need-help)

---

## 🌟 Code of Conduct

This project follows a simple principle: **be respectful, inclusive, and constructive**.

- ✅ Welcome newcomers and be patient with questions
- ✅ Give constructive, specific feedback on PRs
- ✅ Credit others' work and ideas
- 🚫 No harassment, discrimination, or personal attacks
- 🚫 No spam or self-promotion unrelated to the project

Violations may result in removal from the project community.

---

## 🧰 How Can I Contribute?

There are many ways to contribute — you don't have to write code!

| Type | Examples |
|---|---|
| 🐛 **Bug Reports** | Found a crash, wrong output, or broken endpoint? Open an issue. |
| ✨ **Feature Requests** | Have an idea for a new embedding provider, UI improvement, or API feature? |
| 📖 **Documentation** | Improve docstrings, README sections, or add usage examples. |
| 🧪 **Tests** | Add test coverage for untested modules or edge cases. |
| 🔢 **Embedding Providers** | Add support for Cohere, Mistral, HuggingFace, etc. |
| 🤖 **LLM Providers** | Add Anthropic Claude, Mistral, Ollama local models, etc. |
| 🎨 **Frontend UX** | Improve the UI, add dark/light theme toggle, better mobile layout. |
| ⚡ **Performance** | Optimize chunking, batching, or retrieval speed. |
| 🔒 **Security** | Improve prompt injection defenses or input sanitization. |

---

## 🛠️ Development Setup

### 1 · Fork & Clone

```bash
# Fork the repo on GitHub first, then:
git clone https://github.com/<your-username>/docurag-ai.git
cd docurag-ai
```

### 2 · Create a Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3 · Install Dependencies

```bash
pip install -r requirements.txt
```

### 4 · Set Up Environment

```bash
cp .env.example .env
# Edit .env and add your API keys if needed (optional — app works offline)
```

### 5 · Verify the Setup

```bash
# Start the server
uvicorn backend.main:app --reload

# In another terminal, run the tests
pytest tests/ -v
```

If all tests pass and the server starts at `http://localhost:8000`, you're ready to contribute!

---

## 📁 Project Structure

```
backend/
├── main.py              ← FastAPI routes — add new endpoints here
├── config.py            ← Add new config settings here
├── models.py            ← Add new Pydantic schemas here
├── ingestion/           ← Document loading, cleaning, chunking
├── embeddings/          ← Add new embedding providers here
├── vectorstore/         ← ChromaDB logic
├── retrieval/           ← Query embedding + similarity search
└── rag/                 ← LLM generation + prompt engineering
    ├── pipeline.py      ← Add new LLM providers here
    └── prompt.py        ← System prompt & injection defenses
frontend/
├── index.html           ← App HTML shell
├── app.js               ← All frontend JS logic
└── style.css            ← Styling
tests/                   ← pytest test suite
```

---

## ✍️ Coding Standards

### Python

- Follow **PEP 8** style guidelines
- Use **type hints** on all function signatures
- Write **docstrings** for all public classes and methods
- Keep functions focused — one responsibility per function
- Use **Pydantic models** for all API request/response schemas
- Prefer explicit imports over wildcard imports (`from x import *`)
- Handle exceptions explicitly — avoid bare `except:` clauses

```python
# ✅ Good
def embed_query(self, text: str) -> List[float]:
    """Generate an embedding vector for a single user query.

    Args:
        text: The raw query string.

    Returns:
        A list of floats representing the embedding vector.
    """
    ...

# 🚫 Avoid
def embed_query(self, text):
    ...
```

### Adding a New Embedding Provider

1. Create a class inheriting from `BaseEmbeddingProvider` in `backend/embeddings/embedding_service.py`
2. Implement `dimension`, `provider_name`, `embed_documents()`, and `embed_query()`
3. Add provider resolution logic in `EmbeddingService._resolve_provider()`
4. Add corresponding config keys to `backend/config.py` and `.env.example`
5. Write tests in `tests/`

### Adding a New LLM Provider

1. Add a new `_generate_<provider>()` method to `LLMClient` in `backend/rag/pipeline.py`
2. Update `LLMClient._resolve_provider()` to detect and return the new provider
3. Add config keys to `backend/config.py` and `.env.example`
4. Write tests in `tests/`

### Frontend (JavaScript)

- Keep all JS in `frontend/app.js` — no external frameworks or bundlers
- Use `async/await` for all `fetch()` calls
- Handle API errors gracefully and display user-friendly messages
- Keep functions small and well-commented

---

## 💬 Commit Message Guidelines

Use the **Conventional Commits** format for all commits:

```
<type>(<scope>): <short summary>
```

| Type | When to use |
|:---:|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes only |
| `style` | Formatting, whitespace (no logic change) |
| `refactor` | Code refactoring (no feature or bug fix) |
| `test` | Adding or updating tests |
| `chore` | Build process, dependency updates |
| `perf` | Performance improvements |
| `security` | Security improvements |

### Examples

```bash
git commit -m "feat(embeddings): add Cohere embedding provider"
git commit -m "fix(chunker): handle empty pages in DOCX files"
git commit -m "docs(readme): add Ollama setup instructions"
git commit -m "test(retriever): add top_k boundary condition tests"
git commit -m "security(prompt): strengthen injection defense patterns"
```

---

## 🔃 Pull Request Process

### Before Submitting

- [ ] Your branch is up-to-date with `main`
- [ ] All existing tests pass: `pytest tests/ -v`
- [ ] New code has corresponding tests
- [ ] Docstrings are added/updated
- [ ] `.env.example` updated if you added new config keys
- [ ] No secrets or API keys committed

### Submitting

1. **Push** your feature branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a Pull Request** on GitHub against the `main` branch

3. **Fill in the PR template** — include:
   - What problem does this solve?
   - What approach did you take?
   - How was it tested?
   - Screenshots for UI changes

4. **Link any related issues** using `Closes #<issue-number>`

### Review Process

- A maintainer will review your PR within a few days
- You may be asked to make changes — this is normal and not a rejection
- Once approved, your PR will be squash-merged into `main`

---

## 🐛 Reporting Bugs

Before opening a bug report:
- Check if the issue already exists in [GitHub Issues](https://github.com/sunbyte16/docurag-ai/issues)
- Try reproducing on the latest `main` branch

When reporting, include:

```markdown
**Describe the bug**
A clear description of what happened vs. what you expected.

**Steps to Reproduce**
1. Upload file '...'
2. Ask question '...'
3. See error

**Environment**
- OS: Windows 11 / macOS / Linux
- Python version: 3.11.x
- LLM provider: openai / gemini / offline
- Embedding provider: openai / gemini / local

**Error Output / Logs**
Paste any relevant logs or stack traces here.
```

---

## 💡 Suggesting Features

Open a [GitHub Issue](https://github.com/sunbyte16/docurag-ai/issues) with:

- **Use case** — what problem does this feature solve?
- **Proposed solution** — how should it work?
- **Alternatives considered** — any other approaches you thought of?
- **Impact** — who would benefit from this?

---

## 🌱 Areas That Need Help

These are active areas where contributions are especially welcome:

| Area | Description | Difficulty |
|---|---|:---:|
| 🔢 **Cohere Embeddings** | Add `CohereEmbeddingProvider` | 🟡 Medium |
| 🤖 **Ollama LLM** | Add local LLM via Ollama API | 🟡 Medium |
| 🔢 **HuggingFace Embeddings** | sentence-transformers support | 🟡 Medium |
| 📊 **Re-ranking** | Add cross-encoder re-ranking stage | 🔴 Hard |
| 🌐 **Streaming Responses** | SSE streaming for long answers | 🟡 Medium |
| 🧪 **More Tests** | Increase test coverage across modules | 🟢 Easy |
| 📖 **Usage Examples** | Jupyter notebooks, example scripts | 🟢 Easy |
| 🎨 **UI Improvements** | Mobile responsiveness, accessibility | 🟡 Medium |
| 🔒 **Auth Layer** | Optional API key authentication | 🔴 Hard |
| 📦 **Docker Setup** | Dockerfile + docker-compose | 🟢 Easy |

---

<div align="center">

---

**Questions?** Open an issue or reach out directly.

<br/>

[![GitHub](https://img.shields.io/badge/GitHub-sunbyte16-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sunbyte16)
&nbsp;
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Sunil_Kumar-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/sunil-kumar-bb88bb31a/)
&nbsp;
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit_Now-FF5722?style=for-the-badge&logo=netlify&logoColor=white)](https://lively-dodol-cc397c.netlify.app)

<br/>

*Made with* ❤️ *by* **𝕊𝕦𝕟𝕚𝕝 𝕊𝕙𝕒𝕣𝕞𝕒**

</div>
