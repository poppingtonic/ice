from structlog.stdlib import get_logger

from ice.paper import Paper
from ice.paper import Paragraph
from ice.recipe import Recipe
from ice.recipes.rank_paragraphs import RankParagraphs

Experiment = str

log = get_logger()


def make_qa_prompt(
    question_short: str,
    question_long: str,
    answer_prefix: str,
    paragraphs: list[Paragraph],
) -> str:
    paragraphs_str = "\n\n".join(map(str, paragraphs))
    return f"""
Answer the question "{question_short}" based on the following paragraphs.

Paragraphs:

{paragraphs_str}

Question: {question_long}

{answer_prefix}
""".strip()


class ComparisonsQA(Recipe):
    name = "ComparisonsQA"

    async def execute(self, **kw):
        paper: Paper = kw["paper"]
        question_short: str = kw.get(
            "question_short",
            "What were the trial arms (subgroups of participants) of the experiment?",
        )
        question_long: str = kw.get(
            "question_long",
            "What were the trial arms (subgroups of participants) of the experiment? List one per line.",
        )
        num_paragraphs: int = kw.get("num_paragraphs", 3)
        answer_prefix = kw.get("answer_prefix", "Answer: The trial arms were:\n-")

        rank_paragraphs = RankParagraphs(mode=self.mode)

        top_paragraphs = await rank_paragraphs.execute(
            paper=paper, question=question_short, n=num_paragraphs
        )

        qa_prompt = make_qa_prompt(
            question_short=question_short,
            question_long=question_long,
            answer_prefix=answer_prefix,
            paragraphs=top_paragraphs,
        )

        answer = await self.agent().answer(
            context="", question=qa_prompt, multiline=True, max_tokens=500
        )

        return answer
