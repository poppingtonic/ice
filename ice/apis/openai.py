import httpx

from httpx import ReadTimeout
from httpx import Timeout
from structlog.stdlib import get_logger
from tenacity import retry
from tenacity import retry_any
from tenacity import retry_if_exception
from tenacity import retry_if_exception_type
from tenacity.wait import wait_random_exponential

from ice.cache import diskcache
from ice.settings import settings
from ice.utils import ProactiveRateLimitError
from ice.utils import token_bucket

log = get_logger()


@token_bucket(1, 6)
async def wait_before_alpha():
    return


class RateLimitError(Exception):
    pass


def log_attempt_number(retry_state):
    if retry_state.attempt_number > 1:
        exception_name = retry_state.outcome.exception().__class__.__name__
        log.warning(
            f"Retrying ({exception_name}): Attempt #{retry_state.attempt_number} ({settings.OPENAI_ORG_ID})..."
        )


class OpenAIAPIClient:
    """A wrapper class for the OpenAI API."""

    RETRYABLE_STATUS_CODES = {408, 429, 502, 503, 504}

    def __init__(self, api_key: str, org_id: str):
        self.api_key = api_key
        self.org_id = org_id
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Organization": self.org_id,
        }

    @staticmethod
    def is_retryable_HttpError(e: BaseException) -> bool:
        return (
            isinstance(e, httpx.HTTPStatusError)
            and e.response.status_code in OpenAIAPIClient.RETRYABLE_STATUS_CODES
        )

    @retry(
        retry=retry_any(
            retry_if_exception(is_retryable_HttpError),
            retry_if_exception_type(Timeout),
            retry_if_exception_type(ReadTimeout),
            retry_if_exception_type(RateLimitError),
            retry_if_exception_type(ProactiveRateLimitError),
        ),
        wait=wait_random_exponential(min=1),
        after=log_attempt_number,
    )
    async def post(
        self, endpoint: str, json: dict, timeout: float | None = None
    ) -> dict:
        """Send a POST request to the OpenAI API and return the JSON response."""
        if "alpha" in json.get("model", "").lower():
            await wait_before_alpha()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{endpoint}",
                json=json,
                headers=self.headers,
                timeout=timeout,
            )
            if response.status_code == 429:
                raise RateLimitError
            response.raise_for_status()
            return response.json()

    @diskcache()
    async def complete(
        self,
        prompt: str,
        stop: str | None = "\n",
        top_p: float = 1,
        temperature: float = 0,
        model: str = "text-davinci-002",
        max_tokens: int = 256,
        logprobs: int | None = None,
        n: int = 1,
        cache_id: int = 0,  # for repeated non-deterministic sampling using caching
    ) -> dict:
        """Send a completion request to the OpenAI API and return the JSON response."""
        cache_id  # unused
        return await self.post(
            "completions",
            json={
                "prompt": prompt,
                "stop": stop,
                "top_p": top_p,
                "temperature": temperature,
                "model": model,
                "max_tokens": max_tokens,
                "logprobs": logprobs,
                "n": n,
            },
        )


def is_retryable_HttpError(e: BaseException) -> bool:
    return OpenAIAPIClient.is_retryable_HttpError(e)
