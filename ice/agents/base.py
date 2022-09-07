from ice.trace import TracedABC


class Agent(TracedABC):
    async def relevance(
        self,
        *,
        question: str,
        context: str,
        verbose: bool = False,
        default: float | None = None,
    ) -> float:
        raise NotImplementedError

    async def answer(
        self,
        *,
        context: str,
        question: str,
        multiline: bool = False,
        verbose: bool = False,
        default: str = "",
        max_tokens: int | None = None,
    ) -> str:
        raise NotImplementedError

    async def predict(
        self, *, context: str, default: str = "", verbose: bool = False
    ) -> dict[str, float]:
        raise NotImplementedError

    async def prompted_classify(
        self,
        *,
        context: str,
        question: str,
        choices: tuple[str, ...],
        default: str | None = None,
        verbose: bool = False,
    ) -> tuple[str, float, str | None]:
        raise NotImplementedError
