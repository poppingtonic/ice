from ice.apis.anthropic import AI_PROMPT
from ice.apis.anthropic import HUMAN_PROMPT
from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.metrics.gold_standards import list_experiments
from ice.paper import get_full_document_id
from ice.paper import Paper
from ice.recipe import Recipe
from ice.utils import window_by_tokens

QUESTION_SHORT_NAME = "adherence"


def get_paper_text(paper: Paper) -> str:
    return "\n\n".join(str(p) for p in paper.paragraphs)


def generate_qa_prompt(paper_text: str) -> str:
    return f"""
{HUMAN_PROMPT} I'm trying to evaluate some RCTs. Right now I want to summarize the participant funnel. Can you explain the concept of a participant funnel?
{AI_PROMPT} Sure, the participant funnel describes how many participants are in the study at each stage. The stages vary by study, but they sometimes include an intended sample size, the size of the sample at randomization, the number of participants who actually received the intervention, and the number of participants included in the final analysis.
{HUMAN_PROMPT} Here's the text of a paper I've been thinking about. Can you read it and summarize the participant funnel for this study? Be sure to only include information that is explicitly in the paper.

{paper_text}
{AI_PROMPT} Let's think step-by-step, starting with the initial sample size or sizes. In this paper,"""


def generate_qa_prompt_instruct(paper_text: str) -> str:
    return f"""
Summarize the adherence rate of this research paper based on the following excerpt. If the adherence rate is not mentioned in this excerpt, say "not mentioned".

BEGIN PAPER EXCERPT

{paper_text}

END PAPER EXCERPT

One possible summary of the adherence rate based on the above excerpt is:""".strip()


def create_recipe_result(paper_id: str, experiment: str, answer: str) -> RecipeResult:
    return RecipeResult(
        document_id=paper_id,
        question_short_name=QUESTION_SHORT_NAME,
        experiment=experiment,
        classifications=[
            None,
            None,
        ],
        answer=answer,
        result=answer,
        excerpts=[],
    )


class FunnelSimple(Recipe):
    async def run(self, paper: Paper):
        full_paper_text = get_paper_text(paper)

        descriptions = []
        # Ask the agent to answer the prompt
        for chunk in window_by_tokens(full_paper_text, max_tokens=5000):
            description = await self.agent(
                # "instruct"
                "anthropic-junior-h-helpful-v7-s750"
                # "text-alpha"
            ).answer(
                prompt=generate_qa_prompt_instruct(chunk),
                multiline=True,
                max_tokens=500,
            )
            descriptions.append(description)

        # Save results for each experiment
        paper_id = get_full_document_id(paper.document_id)
        experiments: list[str] = list_experiments(document_id=paper_id)
        recipe_results = [
            create_recipe_result(paper_id, experiment, "\n---\n".join(descriptions))
            for experiment in experiments
        ]
        self.maybe_add_to_results(recipe_results)

        return "\n\n---\n\n".join(descriptions)
