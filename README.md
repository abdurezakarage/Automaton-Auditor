### Automaton Auditor (Week 2)

This repository implements the **Digital Courtroom** for TRP1 Week 2: a LangGraph-based swarm that audits a target GitHub repo + PDF report and produces a structured Markdown audit.

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

