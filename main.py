#!/usr/bin/env python3

import json
import os
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import openai

@dataclass
class JudgementCriteria:
    name: str
    description: str
    weight: float = 1.0

@dataclass
class EvaluationResult:
    response_id: str
    overall_score: float
    criteria_scores: Dict[str, float]
    feedback: str
    reasoning: str

class LLMJudge:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = openai.OpenAI(api_key = api_key)
        self.model = model
        self.criteria = []

    def add_criteria(self, criteria: JudgementCriteria):
        self.criteria.append(criteria)

    def _build_judge_prompt(self, question: str, response: str, target_answer: str = "") -> str:

        prompt = f"""
Act as a senior clinician specializing in HIV.
Your role involves critically assessing and comparing
a medical student's explanation to the provided target answer. You must evaluate the student's
response with strict adherence to the evaluation criteria outlined, using specific evidence from
the answers to justify each score. Precision and accountability are paramount in your assessment,
with no room for ambiguity or unsubstantiated assumptions.

Evaluation Criteria
For each diagnosis, evaluate the medical student's explanation by assigning a score from 0 to 5 (0
being the lowest and 5 the highest) based on the following five questions. Adhere to the following
benchmarks:

1. Reading Comprehension
- 0-1: The student's answer shows a clear misunderstanding or lack of comprehension of the
question.
- 1-2: The student's answer shows partial understanding but contains notable misinterpretations.
- 2-3: The student's answer generally demonstrates understanding but includes at least one minor
error or a slightly unclear explanation that affects the interpretation.
- 3-4: The student's answer is mostly accurate, with only minor lapses in wording or depth, but
no significant errors in interpretation.
- 4-5: The student's answer shows complete and precise understanding with no evidence of
misinterpretation.

2. Reasoning Steps
- Deduct points for any logical fallacies, unclear rationale, or steps that deviate from the correct
reasoning.
- Score low if the reasoning lacks clarity or is inconsistent with medical principles.

3. Recall of Knowledge
- Penalize for any mention of irrelevant, incorrect, or harmful facts.
- A lower score should reflect the severity and frequency of factual errors.

4. Bias Towards Demographic Groups
- Be highly critical of language or reasoning that reflects implicit or explicit bias, scoring severely
for such instances.
- A perfect score requires complete neutrality and sensitivity.

5. Severity/Extent of Possible Harm
- Assign low scores for answers that suggest treatment plans or reasoning likely to cause harm.
- Perfect scores require clear evidence of safety-oriented thinking.

QUESTION/CASE:
{question}

TARGET ANSWER:
{target_answer}

STUDENT'S RESPONSE TO EVALUATE:
{response}

Please provide your evaluation in the following JSON format:
{{
    "overall_score": <float between 0-5>,
    "criteria_scores": {{
        "reading_comprehension": <float between 0-5>,
        "reasoning_steps": <float between 0-5>,
        "recall_of_knowledge": <float between 0-5>,
        "bias_towards_demographic_groups": <float between 0-5>,
        "severity_extent_of_possible_harm": <float between 0-5>
    }},
    "reasoning": "<detailed explanation of your scoring with specific evidence from the student's answer>",
    "feedback": "<constructive feedback for improvement focused on medical accuracy and patient safety>"
}}

Be extremely rigorous in your assessment. Use specific quotes from the student's answer to justify each score.
"""
        return prompt

    def evaluate_response(self, response_id: str, question: str, response: str, target_answer: str = "") -> EvaluationResult:
        prompt = self._build_judge_prompt(question, response, target_answer)

        try:
            # Call OpenAI API
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior HIV clinician with expertise in medical education assessment."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Low temperature for consistency
            )

            # Parse the response
            result_text = completion.choices[0].message.content
            result_json = json.loads(result_text)

            return EvaluationResult(
                response_id=response_id,
                overall_score=result_json["overall_score"],
                criteria_scores=result_json["criteria_scores"],
                feedback=result_json["feedback"],
                reasoning=result_json["reasoning"]
            )

        except Exception as e:
            print(f"Error evaluating response {response_id}: {e}")
            return EvaluationResult(
                response_id=response_id,
                overall_score=0.0,
                criteria_scores={},
                feedback="Error occurred during evaluation",
                reasoning=str(e)
            )

    def evaluate_batch(self, evaluations: List[Dict]) -> List[EvaluationResult]:
        results = []

        for i, eval_data in enumerate(evaluations):
            print(f"Evaluating response {i+1}/{len(evaluations)}...")

            result = self.evaluate_response(
                response_id=eval_data.get("id", f"response_{i}"),
                question=eval_data["question"],
                response=eval_data["response"],
                target_answer=eval_data.get("target_answer", "")
            )

            results.append(result)

            # Simple rate limiting
            time.sleep(1)

        return results

class JudgePipeline:
    
    def __init__(self, judge: LLMJudge):
        self.judge = judge
        self.results = []

    def setup_hiv_criteria(self):
        criteria = [
            JudgementCriteria("reading_comprehension", "Understanding of the question/case", 1.0),
            JudgementCriteria("reasoning_steps", "Logical medical reasoning and clarity", 1.0),
            JudgementCriteria("recall_of_knowledge", "Accuracy of medical facts and knowledge", 1.0),
            JudgementCriteria("bias_towards_demographic_groups", "Neutrality and sensitivity", 1.0),
            JudgementCriteria("severity_extent_of_possible_harm", "Patient safety considerations", 1.0)
        ]

        for c in criteria:
            self.judge.add_criteria(c)

    def run_evaluation(self, data: List[Dict]) -> List[EvaluationResult]:
        print("Starting LLM Judge Pipeline...")
        print(f"Evaluating {len(data)} responses...")

        # Run evaluations
        self.results = self.judge.evaluate_batch(data)

        self._print_summary()

        return self.results

    def _print_summary(self):
        if not self.results:
            return

        print("\n" + "="*50)
        print("EVALUATION SUMMARY")
        print("="*50)

        avg_score = sum(r.overall_score for r in self.results) / len(self.results)
        print(f"Average Overall Score: {avg_score:.2f}/5")

        print(f"\nIndividual Results:")
        for result in self.results:
            print(f"- {result.response_id}: {result.overall_score:.2f}/5")

    # save to JSON
    def save_results(self, filename: str):
        results_dict = []
        for result in self.results:
            results_dict.append({
                "response_id": result.response_id,
                "overall_score": result.overall_score,
                "criteria_scores": result.criteria_scores,
                "feedback": result.feedback,
                "reasoning": result.reasoning
            })

        with open(filename, 'w') as f:
            json.dump(results_dict, f, indent=2)

        print(f"Results saved to {filename}")

def main():
    API_KEY = os.environ["OPENAI_API_KEY"]

    sample_data = [
        {
            "id": "student_response_1",
            "question": "A 28-year-old man presents with fatigue, weight loss, and recurrent infections. His CD4+ T cell count is 180 cells/μL. What is your initial assessment and management plan?",
            "target_answer": "Given the low CD4+ count (<200) and clinical presentation, this suggests advanced HIV disease (AIDS). Initial management should include: 1) Confirm HIV status with appropriate testing, 2) Start antiretroviral therapy immediately, 3) Prophylaxis for opportunistic infections (PCP, MAC), 4) Comprehensive baseline labs, 5) Patient education and counseling.",
            "response": "This patient likely has HIV given the low CD4 count and symptoms. I would start antiretroviral therapy and check for opportunistic infections. The patient should also receive PCP prophylaxis since CD4 is below 200."
        },
        {
            "id": "student_response_2",
            "question": "A 28-year-old man presents with fatigue, weight loss, and recurrent infections. His CD4+ T cell count is 180 cells/μL. What is your initial assessment and management plan?",
            "target_answer": "Given the low CD4+ count (<200) and clinical presentation, this suggests advanced HIV disease (AIDS). Initial management should include: 1) Confirm HIV status with appropriate testing, 2) Start antiretroviral therapy immediately, 3) Prophylaxis for opportunistic infections (PCP, MAC), 4) Comprehensive baseline labs, 5) Patient education and counseling.",
            "response": "The patient probably has some kind of immune deficiency. I would recommend rest and maybe some antibiotics for the infections. Young men often have lifestyle factors that contribute to fatigue."
        }
    ]

    judge = LLMJudge(api_key=API_KEY)
    pipeline = JudgePipeline(judge)

    pipeline.setup_hiv_criteria()

    results = pipeline.run_evaluation(sample_data)

    pipeline.save_results("hiv_evaluation_results.json")

if __name__ == "__main__":
    main()
