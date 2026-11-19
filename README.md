# AI Regimen — Synthetic Evidence Review Research

AI Regimen is a research-only application for exploring evidence grounding, lexical claim screening, optional LLM evaluation, adversarial tests, human annotation, reproducibility and release governance. The project evolved from an early `LLM-as-Judge` medical-response grading proof of concept (still available in `main.py`).

**Safety boundary:** This is not a clinical decision-support tool, validated medical evaluator, diagnostic system or prescribing assistant. Use fictional data only. A `synthetic: true` flag does not automatically remove personal health information. Fixture labels and reviewer agreement do not establish medical correctness.

## What's built

| Area | Implemented functionality |
| --- | --- |
| Guided demo | Four-step, no-backend walkthrough with six fictional evidence challenges, explanation reveal, illustrative governance timeline and local JSON results export |
| Live demo extensions | Optional read-only connection to deterministic lexical evaluation, offline model-status comparison and operator-enabled human-review summary |
| Research overview | Integrated dashboard at `/judge/overview` with lexical screening, model availability, human review and process quality gates |
| Synthetic case review | Validated fictional HIV case inputs, completeness review and evidence-dependent assessment with conservative abstention |
| Evidence management | Operator-reviewed source snapshots, structured guideline parsing, provenance metadata and local evidence search |
| Claim evaluation | Deterministic lexical grounding, synthetic benchmark, optional model-judge adapter and lexical/model comparison |
| Adversarial benchmark | Twelve fictional claim/evidence pairs testing negation, quantity, uncertainty, scope, time, entity and causality |
| Research annotation | Local synthetic reviewer labels, disagreement analysis, inter-rater reliability and conservative quality gates |
| Reproducibility | Experiment history, evaluation reports, regression comparisons, CI-generated synthetic artifacts and history dashboards |
| Release governance | Release-readiness checks, manifests, local release registry, research audit trail and audit integrity checks |

The dashboards are **read-only**. Model execution is not automatically enabled. Human review, quality-gate, registry and audit endpoints are disabled unless explicitly configured. Some UI examples are deliberately simulated and are labeled as such.

## Stack

- Python, FastAPI and Pydantic for research APIs and validation
- Next.js 15, React 19 and TypeScript for the frontend
- Python `unittest`, Next.js production build and GitHub Actions for automated checks
- Local files/JSONL for research history, annotations and release metadata

## Quick start

Requirements: Python 3 and Node.js with npm.

```bash
git clone https://github.com/MikeTerekhov/llm-as-judge.git
cd llm-as-judge
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-api.txt
python -m uvicorn api.app:app --reload --port 8000
```

In a second terminal:

```bash
cd llm-as-judge/frontend
npm install
npm run dev
```

Visit:

- `http://localhost:3000/demo` — guided demo; works without the API
- `http://localhost:3000/judge/overview` — integrated research overview; API required for live sections
- `http://localhost:3000/judge` — benchmark and model-status workspace
- `http://localhost:3000/judge/adversarial` — fictional adversarial benchmark
- `http://localhost:3000/` — synthetic case review; API and configured evidence snapshots required

Frontend API origin defaults to `http://localhost:8000`; override with `NEXT_PUBLIC_API_URL` when necessary. The FastAPI health endpoint is `http://localhost:8000/health`.

## Research endpoints

| Endpoint | Behavior |
| --- | --- |
| `GET /api/v1/judge/benchmark` | Static fictional lexical benchmark |
| `GET /api/v1/judge/comparison` | Read-only lexical/model comparison; no model invoked |
| `GET /api/v1/judge/adversarial` | Twelve deterministic fictional stress tests |
| `GET /api/v1/judge/adversarial-model` | Read-only model benchmark status; no model invoked |
| `GET /api/v1/judge/adjudication` | Optional local synthetic reviewer summary |
| `GET /api/v1/judge/reliability` | Optional inter-rater reliability |
| `GET /api/v1/judge/quality-gates` | Optional process quality gates |
| `GET /api/v1/judge/release-registry` | Optional local release registry |
| `GET /api/v1/judge/audit-trail` | Optional research audit metadata |
| `POST /api/v1/cases/review` | Validate fictional case completeness |
| `POST /api/v1/cases/assess` | Evidence-dependent synthetic assessment; may abstain |

For local review endpoints, set `AI_REGIMEN_ENABLE_REVIEW_API=true` and `AI_REGIMEN_REVIEW_PATH` to an operator-managed synthetic review JSONL file. Registry and audit APIs have their own disabled-by-default environment controls. Do not expose operator files or endpoints publicly without appropriate authentication and security review.

## Verification

```bash
python -m unittest discover -s tests -v
cd frontend
npm run build
```

GitHub Actions also runs synthetic evaluation checks and regression comparisons. The default human-review quality gate may remain blocked because CI does not supply human reviewers; this is intentional, not evidence of clinical readiness.

## Project history and documentation

Milestone implementation notes are under `docs/AR-*.md`, covering the research pipeline, benchmark fixtures, quality gates, audit integrity and guided demo. The original `main.py` workflow uses an OpenAI API key and is **separate from** the read-only Next.js/FastAPI research dashboards; do not assume that viewing the dashboard calls GPT-4o.

## Limitations

The current lexical evaluator is a screening heuristic, not a semantic entailment model. Hand-authored fictional labels are not independently verified ground truth. Reviewer consensus is not accuracy. Audit hashes and manifest checksums provide integrity checks, not authenticated signatures or clinical approval. No real patient data, diagnosis, treatment recommendation or prescribing is supported.
