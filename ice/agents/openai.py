import math

from typing import Any

from structlog.stdlib import get_logger

from ice.agents.base import Agent
from ice.apis.openai import OpenAIAPIClient
from ice.environment import env
from ice.settings import settings
from ice.utils import longest_common_prefix

log = get_logger()


class OpenAIAgent(Agent):
    """An agent that uses the OpenAI API to generate answers and predictions."""

    def __init__(
        self,
        model: str = "text-davinci-002",
        temperature: float = 0.0,
        top_p: float = 1.0,
    ):
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.client = OpenAIAPIClient(
            api_key=settings.OPENAI_API_KEY, org_id=settings.OPENAI_ORG_ID
        )

    async def answer(
        self,
        *,
        prompt: str,
        multiline: bool = False,
        verbose: bool = False,
        default: str = "",
        max_tokens: int | None = None,
    ) -> str:
        """Generate an answer to a question given some context."""
        if verbose:
            self._print_markdown(prompt)
        stop = None if multiline else "\n"
        response = await self._complete(prompt, stop=stop, max_tokens=max_tokens)
        answer = self._extract_answer(response)
        if verbose:
            self._print_markdown(answer)
        return answer

    async def predict(self, *, context, default="", verbose=False) -> dict[str, float]:
        """Generate a probability distribution over the next token given some context."""
        if verbose:
            self._print_markdown(context)
        response = await self._complete(context, logprobs=5, max_tokens=1)
        prediction = self._extract_prediction(response)
        if verbose:
            self._print_markdown(prediction)
        return prediction

    async def classify(
        self,
        *,
        prompt: str,
        choices: tuple[str, ...],
        default: str | None = None,
        verbose: bool = False,
    ) -> tuple[str, float, str | None]:
        """Generate a classification from a list of choices given some context and a question."""
        if verbose:
            self._print_markdown(prompt)
            self._print_markdown(choices)

        choice_prefix = longest_common_prefix(choices).rstrip()
        prompt_with_prefix = f"{prompt}{choice_prefix}"

        if prompt_with_prefix.endswith(" "):
            prompt_with_prefix = prompt_with_prefix[:-1]
            default = " "
        else:
            default = ""

        prediction = await self.predict(context=prompt_with_prefix, default=default)

        rel_probs = self._compute_relative_probs(choices, choice_prefix, prediction)

        most_likely_choice = max(choices, key=lambda choice: rel_probs[choice])

        if verbose:
            self._print_markdown(most_likely_choice)

        return most_likely_choice, rel_probs[most_likely_choice], None

    async def _complete(self, prompt, **kwargs) -> dict:
        """Send a completion request to the OpenAI API with the given prompt and parameters."""
        kwargs.update(
            {
                "model": self.model,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "n": 1,
            }
        )
        response = await self.client.complete(prompt, **kwargs)
        if "choices" not in response:
            raise ValueError(f"No choices in response: {response}")
        return response

    def _extract_answer(self, response: dict) -> str:
        """Extract the answer text from the completion response."""
        return response["choices"][0]["text"].strip()

    def _extract_prediction(self, response: dict) -> dict[str, float]:
        """Extract the prediction dictionary from the completion response."""
        answer = response["choices"][0]["logprobs"]["top_logprobs"][0]
        return {k: math.exp(p) for (k, p) in answer.items()}

    def _compute_relative_probs(
        self, choices: tuple[str, ...], choice_prefix: str, prediction: dict[str, float]
    ) -> dict[str, float]:
        """Compute the relative probabilities of the choices based on the prediction."""

        def lookup_prob(choice: str):
            scores = 0.0
            for (token, prob) in prediction.items():
                if choice[len(choice_prefix) :].startswith(token):
                    scores += prob
            return scores

        abs_probs = {choice: lookup_prob(choice) for choice in choices}
        Z = sum(abs_probs.values())
        if Z < 0.8:
            log.warning(f"{1-Z} of unaccounted probability in classify")
            log.warning(choice_prefix)
            log.warning(str(prediction))
            log.warning(str(abs_probs))

        rel_probs = {choice: prob / Z for (choice, prob) in abs_probs.items()}
        return rel_probs

    def _print_markdown(self, obj: Any):
        """Print the text with markdown formatting."""
        env().print(obj, format_markdown=True)
