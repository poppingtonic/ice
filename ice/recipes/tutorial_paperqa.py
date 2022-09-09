from ice.paper import Paper
from ice.paper import Paragraph
from ice.recipe import Recipe
from ice.recipes.tutorial_qa import QA
from ice.utils import map_async


def make_classification_prompt(paragraph: Paragraph, question: str) -> str:
    return f"""Here is a paragraph from a research paper: "{paragraph}"

Question: Does this paragraph answer the question '{question}'? Say Yes or No.
Answer:"""


class PaperQA(Recipe):
    async def classify_paragraph(self, paragraph: Paragraph, question: str) -> float:
        choice, choice_prob, _ = await self.agent().classify(
            question=make_classification_prompt(paragraph, question),
            choices=(" Yes", " No"),
        )
        return choice_prob if choice == " Yes" else 1 - choice_prob

    async def get_relevant_paragraphs(
        self, paper: Paper, question: str, top_n: int = 3
    ) -> list[Paragraph]:
        probs = await map_async(
            paper.paragraphs, lambda par: self.classify_paragraph(par, question)
        )
        sorted_pairs = sorted(
            zip(paper.paragraphs, probs), key=lambda x: x[1], reverse=True
        )
        return [par for par, prob in sorted_pairs[:top_n]]

    async def run(self, paper: Paper, question: str = "What was the study population?"):
        relevant_paragraphs = await self.get_relevant_paragraphs(paper, question)
        relevant_str = "\n\n".join(str(p) for p in relevant_paragraphs)
        answer = await QA().run(context=relevant_str, question=question)
        return answer
