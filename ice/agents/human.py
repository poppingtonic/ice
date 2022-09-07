from ice.agents.base import Agent
from ice.environment import env


class HumanAgent(Agent):
    async def answer(
        self,
        *,
        context,
        question,
        multiline=False,
        verbose=False,
        default="",
        max_tokens: int | None = None,
    ) -> str:
        verbose  # ignored for HumanAgent
        completion = await env().answer(
            context + question, default=default, multiline=multiline
        )
        return completion

    async def relevance(self, question, context, verbose=False, default=None) -> float:
        verbose  # ignored for HumanAgent
        score = await env().score(question, context, default=default)
        return score

    async def predict(
        self, *, context: str, default="", verbose=False
    ) -> dict[str, float]:
        verbose  # ignored for HumanAgent
        completion = await env().answer(context, default=default, multiline=False)
        return {completion: 1.0}

    async def prompted_classify(
        self,
        *,
        context: str,
        question: str,
        choices: tuple[str, ...],
        default: str | None = None,
        verbose: bool = False,
    ) -> tuple[str, float, str | None]:
        choice = await env().select(
            prompt=context + question, choices=list(choices), default=default
        )
        return choice, 1.0, None
