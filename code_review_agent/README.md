# 🤖 Autonomous Code Review & Debugging Agent

An AI-powered code review agent that automatically analyzes GitHub repositories, identifies bugs, suggests fixes, and validates them in a sandboxed environment.

## 🚀 Features

- **Repository Ingestion** — Accepts a GitHub URL, clones the repo, and reads all `.py` files.
- **Static Analysis** — Runs [Bandit](https://bandit.readthedocs.io/) (security) and [Pylint](https://pylint.readthedocs.io/) (style/errors) for automated linting.
- **LLM-Powered Bug Detection** — Uses Google Gemini / Claude / GPT-4 to detect logic bugs and suggest targeted fixes.
- **Sandboxed Test Execution** — Runs the project's `pytest` suite inside an [E2B](https://e2b.dev/) sandbox for safe, isolated execution.
- **Auto-Generated Unit Tests** — Generates new unit tests for uncovered functions using an LLM.
- **Fix Validation** — Automatically re-runs tests after applying fixes to confirm correctness.
- **Structured Report** — Produces a comprehensive JSON review report with findings, fixes, and test results.
- **Streamlit Dashboard** — Interactive UI to submit repos, monitor progress, and explore results.

## 🛠️ Tech Stack

| Component          | Technology                          |
|--------------------|-------------------------------------|
| Language           | Python 3.11                         |
| Agent Framework    | LangGraph (LangChain)               |
| LLM                | Google Gemini / Claude 3.5 / GPT-4  |
| Sandbox            | E2B SDK                             |
| Git Operations     | GitPython                           |
| Security Analysis  | Bandit                              |
| Style Analysis     | Pylint                              |
| Testing            | pytest, coverage.py                 |
| UI                 | Streamlit                           |

## 📁 Project Structure

```
code_review_agent/
├── agent/
│   ├── __init__.py          # Agent package init
│   ├── graph.py             # LangGraph StateGraph definition
│   ├── state.py             # State schema (TypedDict)
│   ├── nodes.py             # Each node function in the graph
│   └── prompts.py           # All LLM prompt templates
├── tools/
│   ├── __init__.py          # Tools package init
│   ├── repo_loader.py       # GitHub cloning + file reader
│   ├── static_analysis.py   # Bandit + Pylint wrappers
│   ├── test_runner.py       # pytest + coverage in E2B sandbox
│   ├── fix_generator.py     # LLM-based fix generation
│   └── test_generator.py    # LLM-based test generation
├── sandbox/
│   └── e2b_client.py        # E2B sandbox wrapper
├── report/
│   └── report_builder.py    # Assembles final JSON/PDF report
├── ui/
│   └── app.py               # Streamlit application
├── tests/
│   └── test_tools.py        # Project tests
├── .env.example              # Required API keys template
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## ⚡ Quick Start

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd code_review_agent
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 3. Run the Streamlit UI

```bash
streamlit run ui/app.py
```

## 🔑 Environment Variables

See [`.env.example`](.env.example) for all required API keys:

| Variable              | Description                              |
|-----------------------|------------------------------------------|
| `GOOGLE_API_KEY`      | Google Gemini API key                    |
| `OPENAI_API_KEY`      | OpenAI API key (optional, for GPT-4)     |
| `ANTHROPIC_API_KEY`   | Anthropic API key (optional, for Claude) |
| `E2B_API_KEY`         | E2B sandbox API key                      |
| `GITHUB_TOKEN`        | GitHub personal access token (optional)  |

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.
