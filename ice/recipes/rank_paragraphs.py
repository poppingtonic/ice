import math

from structlog.stdlib import get_logger
from tqdm import tqdm

from ice.paper import Paper
from ice.paper import Paragraph
from ice.recipe import Recipe
from ice.utils import nsmallest_async

log = get_logger()


def make_compare_paragraphs_prompt(a: Paragraph, b: Paragraph, question: str) -> str:
    return f"""
Which of paragraphs A and B better answers the question "{question}"?

Paragraph A: {a}

Paragraph B: {b}

Question: Which of paragraphs A and B better answers the question '{question}'? Answer with "Paragraph A" or "Paragraph B".

Answer: Paragraph""".strip()


class RankParagraphs(Recipe):
    name = "RankParagraphs"

    async def execute(self, **kw) -> list[Paragraph]:
        """
        Rank the paragraphs by how well they answers the question
        using binary search, repeatedly asking the question "Which of
        paragraphs A and B better answer question Q?"
        """

        paper: Paper = kw["paper"]
        if self.mode == "test":
            question = "What are the interventions?"
        else:
            question = kw["question"]
        n: int = kw.get("n", 5)

        async def cmp(a: Paragraph, b: Paragraph) -> int:
            progress_bar.update(1)
            answer = (
                await self.agent().answer(
                    context="",
                    question=make_compare_paragraphs_prompt(a, b, question),
                    multiline=False,
                    max_tokens=1,
                )
            ).strip()
            if answer == "A":
                return -1
            if answer == "B":
                return 1
            log.warning(f"Unrecognized answer: {answer}")
            return 0

        paragraphs = paper.nonempty_paragraphs()

        num_estimated_comparisons = int(len(paragraphs) * math.log2(n))
        with tqdm(total=num_estimated_comparisons) as progress_bar:
            ranked_paragraphs = await nsmallest_async(n, paragraphs, cmp)

        return ranked_paragraphs
