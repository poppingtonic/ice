from ice.agents.base import Agent
from ice.environment import env
from ice.utils import quoted


class AugmentedAgent(Agent):
    def __init__(self, human: Agent, machine: Agent):
        self.human = human
        self.machine = machine

    async def relevance(
        self, *, question, context, verbose=False, default=None
    ) -> float:
        machine_resp = await self.machine.relevance(
            question=question, context=context, verbose=verbose
        )
        human_resp = await self.human.relevance(
            question=question, context=context, verbose=verbose, default=machine_resp
        )
        return human_resp

    async def answer(
        self,
        *,
        prompt: str,
        multiline: bool = False,
        verbose: bool = False,
        default: str = "",
        max_tokens: int | None = None,
    ):
        machine_resp = await self.machine.answer(
            prompt=prompt,
            multiline=multiline,
            verbose=verbose,
            default=default,
            max_tokens=max_tokens,
        )
        return await self.human.answer(
            prompt=prompt,
            multiline=multiline,
            verbose=verbose,
            default=machine_resp,
            max_tokens=max_tokens,
        )

    async def predict(self, *, context, default="", verbose=False) -> dict[str, float]:
        machine_resp: dict[str, float] = await self.machine.predict(
            context=context, verbose=verbose
        )
        # Extract most likely response from machine_resp and use it as default for human.
        most_likely_token = max(machine_resp, key=lambda k: machine_resp[k])
        human_resp = await self.human.predict(
            context=context, default=most_likely_token, verbose=verbose
        )
        return human_resp

    async def classify(
        self,
        *,
        context: str = "",
        question: str,
        choices: tuple[str, ...],
        default: str | None = None,
        verbose: bool = False,
    ) -> tuple[str, float, str | None]:
        (machine_choice, machine_prob, explanation,) = await self.machine.classify(
            context=context,
            question=question,
            choices=choices,
            default=default,
            verbose=verbose,
        )
        if explanation is not None:
            # TODO: Should present this to the human in a way that does
            #       not circumvent agent abstraction
            env().print(
                f"""
#### classify

Machine choice:

{quoted(machine_choice)}

Probability of machine choice:

> {machine_prob:.2f}

Explanation for machine choice:

{quoted(explanation)}""",
                format_markdown=True,
            )
        return await self.human.classify(
            context=context,
            question=question,
            choices=choices,
            default=machine_choice,
            verbose=verbose,
        )
