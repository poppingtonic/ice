import dataclasses
import datetime
import json
import urllib.parse

from collections.abc import Sequence

from httpx import TimeoutException
from pydantic.json import pydantic_encoder
from structlog.stdlib import get_logger
from tenacity import retry
from tenacity.retry import retry_any
from tenacity.retry import retry_if_exception_type
from tenacity.wait import wait_random_exponential
from websockets import client

from ice.cache import diskcache
from ice.settings import settings

log = get_logger()


AI_PROMPT: str = "\nAssistant:"

HUMAN_PROMPT: str = "\nHuman:"

CONVERSATION_BREAK: str = "\n-----\n"

DEFAULT_RLHF_STOP_SEQS: Sequence[str] = [
    HUMAN_PROMPT,
    "-----",
    CONVERSATION_BREAK,
    "---",
    AI_PROMPT,
    " -----",
    "  ------",
    "   ------",
    " ---",
    "  ---",
    "   ---",
    "  -",
    "-  Assistant",
    "  Assistant",
    "-  ASSISTANT",
    "  ASSISTANT",
]


def log_attempt_number(retry_state):
    if retry_state.attempt_number > 1:
        exception_name = retry_state.outcome.exception().__class__.__name__
        log.warning(
            f"Retrying ({exception_name}): Attempt #{retry_state.attempt_number}..."
        )


def require_anthropic_api_key():
    if settings.ANTHROPIC_API_KEY is None:
        raise RuntimeError(
            "ANTHROPIC_API_KEY must be set to use Anthropic models. See the README."
        )


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code.

    https://stackoverflow.com/a/22238613
    """

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    elif dataclasses.is_dataclass(obj):
        return pydantic_encoder(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


class AnthropicError(Exception):
    pass


class AnthropicAPIClient:
    """A wrapper class for the Anthropic API."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "junior-h-helpful-v7-s750",
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = (
            f"wss://{settings.ANTHROPIC_BACKEND}/model/{self.model_name}/sample"
        )

    @diskcache()
    async def complete(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float = 0.0,
        top_p: float = 1.0,
    ):
        return await self._complete(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

    @retry(
        retry=retry_any(
            retry_if_exception_type(TimeoutException),
            retry_if_exception_type(AnthropicError),
        ),
        wait=wait_random_exponential(min=1),
        after=log_attempt_number,
    )
    async def _complete(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float = 0.0,
        top_p: float = 1.0,
    ):
        async for sample in self.async_sample(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        ):
            response = sample["completion"]
        answer = "".join(response)
        return answer

    async def async_sample(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float = 0.0,
        top_p: float = 1.0,
    ):
        """Streaming sample from model."""
        require_anthropic_api_key()

        auth: dict[str, str] = {
            "key": f"Basic {self.api_key}",
            "xAnthropicAuthType": "GITHUB",
        }
        async with client.connect(
            f"{self.base_url}?{urllib.parse.urlencode(auth)}",
            extra_headers=list(auth.items()),
        ) as ws:
            # TODO: Expose more parameters
            request = {
                "q": prompt,  # Prompt
                "t": temperature,  # temperature
                "k": -1,  # top k
                "p": top_p,  # top p
                "n": max_tokens,  # max tokens
                "stop": DEFAULT_RLHF_STOP_SEQS,  # Stop sequences
                "meta": True,  # Skip sampling meta tokens.
                "max_simultaneous_queries": 20,  # should be ~20
                "use_sample_v1": True,  # Always set to True
            }
            await ws.send(json.dumps(request))

            while True:
                response: dict = json.loads(await ws.recv())
                if e := response.get("exception"):
                    log.warning("Anthropic exception:", exception=e)
                    raise AnthropicError

                yield response
                # Break out of the loop once we get back a `stop_reason`
                if response["stop_reason"]:
                    break
