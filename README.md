### Automaton Auditor (Week 2)

This repository implements the **Digital Courtroom**  A LangGraph-based swarm that audits a target GitHub repo + PDF report and produces a structured Markdown audit.

#### High-level structure

- `src/state.py` — Pydantic / TypedDict state definitions and reducers.
- `src/tools/repo_tools.py` — sandboxed git clone, git log extraction, AST-based graph analysis.
- `src/tools/doc_tools.py` — PDF ingestion and query helpers.
- `src/nodes/detectives.py` — RepoInvestigator / DocAnalyst / (later) VisionInspector nodes.
- `src/nodes/judges.py` — Prosecutor, Defense, Tech Lead judge nodes.
- `src/nodes/justice.py` — ChiefJustice synthesis node.
- `src/graph.py` — LangGraph `StateGraph` wiring detectives, judges, and Chief Justice.
- `audit/` — generated Markdown audit reports.
- `reports/` — human-written interim/final PDF reports.

Implementation is guided by `Automaton_Auditor__concept_and_todo.md` in the parent folder.

#### Setup (with uv)

1. Install [`uv`](https://github.com/astral-sh/uv) if you don't have it.
2. From the `automaton-auditor` folder:

```bash
uv sync
```

3. Create `.env` file from `.env.example` template:
   ```bash
   # .env.example is provided - copy it to .env and fill in your keys
   cp .env.example .env
   # Then edit .env with your actual API keys
   ```
   
   Required keys:
   - `OPENROUTER_API_KEY` or `OPENAI_API_KEY` (for LLM calls)
   - `LANGCHAIN_API_KEY` (for LangSmith tracing)
   - `LANGCHAIN_TRACING_V2=true` (enable observability)

#### Running the interim detective graph

From the repo root:

```bash
uv run python run_auditor.py --repo-url "your-repo-url" --pdf-path "pdf-file-path\report.pdf" --mode self --output-name "self_audit.md" 
```

This will:

- Clone the target repo into a sandboxed temp directory.
- Analyze git history and LangGraph wiring (AST-based).
- Ingest the PDF and pull out key orchestration/metacognition passages.
- Print a short summary of repo/doc evidences collected (to be used later by the judges).
