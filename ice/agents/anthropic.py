from structlog.stdlib import get_logger

from ice.agents.base import Agent
from ice.apis.anthropic import AI_PROMPT
from ice.apis.anthropic import AnthropicAPIClient
from ice.apis.anthropic import HUMAN_PROMPT
from ice.environment import env
from ice.settings import settings
from ice.utils import truncate_by_tokens

log = get_logger()


class AnthropicAgent(Agent):
    def __init__(
        self,
        model: str = "junior-h-helpful-v7-s750",
        temperature: float = 0.0,
        top_p: float = 1.0,
    ):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API key not set")
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.client = AnthropicAPIClient(
            api_key=settings.ANTHROPIC_API_KEY,
            model_name=self.model,
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
        if verbose:
            env().print(prompt, format_markdown=True)
        self.validate_prompt(prompt)
        answer = await self.client.complete(
            prompt,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=max_tokens or settings.MAX_ANTHROPIC_TOKENS,
        )
        if verbose:
            env().print(answer, format_markdown=True)
        return answer

    def make_qa_prompt(self, context: str, question: str) -> str:
        # Truncate the context by tokens to avoid exceeding the max length
        context = truncate_by_tokens(context)
        # Format the prompt with the human and AI markers
        return f"""\n{HUMAN_PROMPT} {context}
{AI_PROMPT} I've read it thoroughly and can answer any questions you may have about it.
{HUMAN_PROMPT} {question}
{AI_PROMPT}"""

    def validate_prompt(self, prompt: str, *, max_tokens: int = 7500) -> None:
        # Check for common errors in the prompt and log them as warnings
        problems = []
        if AI_PROMPT not in prompt:
            problems.append(f"'{AI_PROMPT}' not in prompt")
        if HUMAN_PROMPT not in prompt:
            problems.append(f"'{HUMAN_PROMPT}' not in prompt")
        if f"{HUMAN_PROMPT}:" in prompt:
            problems.append(f"Found '{HUMAN_PROMPT}:', expected '{HUMAN_PROMPT}'")
        if f"{AI_PROMPT}:" in prompt:
            problems.append(f"Found '{AI_PROMPT}:', expected '{AI_PROMPT}'")
        max_chars = int(max_tokens * 3.5)
        if len(prompt) > max_chars:
            problems.append(
                f"Prompt length of {len(prompt)} longer than estimated max {max_chars}; consider truncating."
            )
        if problems:
            log.warning(
                "Potential mistakes in Anthropic prompt", issues=problems, prompt=prompt
            )
