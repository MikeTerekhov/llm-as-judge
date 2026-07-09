# LLM-as-Judge: Medical Response Evaluation

A Python pipeline that uses an LLM (GPT-4o) as an automated grader for medical student responses to clinical case questions. It scores each response against a target answer across five weighted criteria and produces structured, evidence-based feedback.

Built as a proof of concept for the "LLM-as-judge" pattern — using a language model with a strict rubric and persona prompt to evaluate free-text answers at scale, instead of relying on manual grading.

## How it works

1. Each response is paired with the original clinical question and a target (reference) answer.
2. `LLMJudge` builds a rubric-driven prompt that instructs the model to act as a senior clinician and grade strictly, citing evidence from the student's answer.
3. The model returns a structured JSON evaluation, which is parsed into an `EvaluationResult`.
4. `JudgePipeline` runs the batch, prints a summary, and saves all results to JSON.

## Evaluation criteria

Each response is scored 0–5 on:

| Criterion | What it measures |
|---|---|
| Reading Comprehension | Understanding of the question/case |
| Reasoning Steps | Logical, medically sound reasoning |
| Recall of Knowledge | Factual accuracy |
| Bias Towards Demographic Groups | Neutrality and sensitivity |
| Severity/Extent of Possible Harm | Patient-safety awareness |

The current example prompt is scoped to HIV case management, but the criteria and prompt template are easy to adapt to other clinical domains.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
```

## Usage

```python
from main import LLMJudge, JudgePipeline
import os

judge = LLMJudge(api_key=os.environ["OPENAI_API_KEY"])
pipeline = JudgePipeline(judge)
pipeline.setup_hiv_criteria()

data = [
    {
        "id": "student_response_1",
        "question": "...",
        "target_answer": "...",
        "response": "...",
    }
]

results = pipeline.run_evaluation(data)
pipeline.save_results("hiv_evaluation_results.json")
```

Running `main.py` directly evaluates two bundled sample responses and writes `hiv_evaluation_results.json`.

## Output

Each evaluation produces:

```json
{
  "response_id": "student_response_1",
  "overall_score": 3.8,
  "criteria_scores": {
    "reading_comprehension": 4,
    "reasoning_steps": 4,
    "recall_of_knowledge": 4,
    "bias_towards_demographic_groups": 5,
    "severity_extent_of_possible_harm": 2
  },
  "reasoning": "...",
  "feedback": "..."
}
```

## Notes

- This is a research/demo project, not a validated clinical or educational assessment tool — LLM-as-judge scores should be spot-checked against human graders before being used for anything high-stakes.
- API keys should be supplied via environment variable, not hardcoded.
