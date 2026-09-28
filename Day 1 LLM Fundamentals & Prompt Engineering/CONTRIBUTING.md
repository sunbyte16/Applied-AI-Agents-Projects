# 🤝 Contributing to PromptLab AI

Thank you for considering contributing! Every improvement — bug fix, new feature, docs update, or prompt strategy — is welcome.

---

## 📋 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [Getting Started](#-getting-started)
- [How to Contribute](#-how-to-contribute)
- [Branch Naming](#-branch-naming)
- [Commit Style](#-commit-style)
- [Pull Request Process](#-pull-request-process)
- [Reporting Bugs](#-reporting-bugs)
- [Suggesting Features](#-suggesting-features)
- [Development Setup](#-development-setup)

---

## 🌟 Code of Conduct

Be respectful, inclusive, and constructive. Harassment or exclusionary behaviour of any kind will not be tolerated.

---

## 🚀 Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
   ```bash
   git clone https://github.com/<your-username>/promptlab-ai.git
   cd promptlab-ai
   ```
3. **Create a virtual environment** and install dependencies
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\Activate.ps1
   # macOS / Linux
   source .venv/bin/activate

   pip install -r requirements.txt
   ```
4. **Copy** `.env.example` → `.env` and add your API key
5. **Run the test suite** to confirm everything is green before making changes
   ```bash
   pytest -v
   ```

---

## 🛠️ How to Contribute

| Type | Description |
|------|-------------|
| 🐛 **Bug Fix** | Fix an existing issue or unexpected behaviour |
| ✨ **New Feature** | Add a new prompting strategy, UI panel, or API endpoint |
| 📖 **Docs** | Improve README, add docstrings, or fix typos |
| 🧪 **Tests** | Add missing test coverage or improve existing tests |
| 🎨 **UI/UX** | Improve the frontend dashboard styling or interactions |
| ⚡ **Performance** | Reduce latency, optimise prompt assembly, improve caching |

---

## 🌿 Branch Naming

Use the following convention:

```
feat/short-description        # new feature
fix/short-description         # bug fix
docs/short-description        # documentation only
test/short-description        # test additions
refactor/short-description    # code cleanup, no behaviour change
```

**Examples:**
```
feat/chain-of-thought-strategy
fix/json-validator-fence-strip
docs/update-api-reference
```

---

## 💬 Commit Style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>
```

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation change |
| `test` | Adding or updating tests |
| `refactor` | Code restructure, no behaviour change |
| `chore` | Tooling, config, dependencies |
| `style` | Formatting, whitespace — no logic change |

**Examples:**
```
feat(prompt_engine): add chain-of-thought strategy builder
fix(llm_service): handle timeout error from Groq provider
docs(README): update architecture diagrams
test(prompt_engine): add edge cases for structured JSON validator
```

---

## 🔀 Pull Request Process

1. Ensure all **18 existing tests pass**: `pytest -v`
2. Add **new tests** for any new behaviour you introduce
3. Update **README.md** if you add or change an API endpoint, strategy, or major feature
4. Open a PR against the `main` branch with:
   - A clear **title** following the commit style
   - A **description** explaining what changed and why
   - Screenshots or output snippets for UI or prompt changes
5. A maintainer will review and provide feedback within a few days

---

## 🐛 Reporting Bugs

Open a [GitHub Issue](https://github.com/sunbyte16) and include:

- [ ] **What happened** — describe the bug clearly
- [ ] **Steps to reproduce** — minimum reproducible example
- [ ] **Expected behaviour** — what should have happened
- [ ] **Environment** — OS, Python version, model used
- [ ] **Error output** — paste the full traceback or console error

---

## 💡 Suggesting Features

Open a [GitHub Issue](https://github.com/sunbyte16) with the label `enhancement` and include:

- **Problem** — what gap or pain point does this address?
- **Proposed solution** — your idea for how to solve it
- **Alternatives considered** — other approaches you thought about
- **Additional context** — mockups, links, or references if relevant

---

## 🧪 Development Setup

```bash
# Run all tests
pytest -v

# Run a specific test file
pytest tests/test_prompt_engine.py -v

# Start the dev server with auto-reload
uvicorn backend.main:app --reload --port 8000

# Open interactive API docs
# http://127.0.0.1:8000/docs
```

---

## 📬 Contact

Have a question before opening an issue?

[![GitHub](https://img.shields.io/badge/GitHub-sunbyte16-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/sunbyte16)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Sunil%20Kumar-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/sunil-kumar-bb88bb31a/)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit%20Site-FF6B6B?style=flat-square&logo=netlify&logoColor=white)](https://lively-dodol-cc397c.netlify.app)

---

<div align="center">

*Made with ❤️ by* **𝕊𝕦𝕟𝕚𝕝 𝕊𝕙𝕒𝕣𝕞𝕒**

</div>
