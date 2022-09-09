import random

from faker import Faker

from ice.agents.base import Agent

random.seed(0)
Faker.seed(0)


class FakeAgent(Agent):
    def __init__(self):
        self.fake = Faker()

    async def relevance(self, *, question, context, verbose=False, default=None):
        return random.random()

    async def answer(
        self,
        *,
        prompt: str,
        multiline: bool = False,
        verbose: bool = False,
        default: str = "",
        max_tokens: int | None = None,
    ):
        return self.fake.sentence()

    async def classify(
        self,
        *,
        prompt: str,
        choices: tuple[str, ...],
        default: str | None = None,
        verbose: bool = False,
    ) -> tuple[str, float, str | None]:
        return random.choice(choices), random.random(), None

    async def predict(
        self, *, context: str, default: str = "", verbose: bool = False
    ) -> dict[str, float]:
        if default:
            words = [default]
        else:
            words = []
        words += [self.fake.word() for _ in range(random.randint(1, 5))]
        return {word: random.random() for word in words}
