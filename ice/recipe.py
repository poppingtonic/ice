from abc import abstractmethod
from collections.abc import Callable
from typing import Generic
from typing import TypeGuard
from typing import TypeVar

from pydantic import BaseSettings
from structlog.stdlib import get_logger

from ice.agent import Agent
from ice.agent import agent_policy
from ice.evaluation.evaluate_recipe_result import EvaluatedRecipeResult
from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.evaluation.evaluation_report import EvaluationReport
from ice.mode import Mode
from ice.trace import TracedABC
from ice.utils import map_async

RecipeSettings = TypeVar("RecipeSettings", bound=BaseSettings)

log = get_logger()


def is_list_of_recipe_result(value: object) -> TypeGuard[list[RecipeResult]]:
    return isinstance(value, list) and all(
        isinstance(item, RecipeResult) for item in value
    )


class Recipe(TracedABC, Generic[RecipeSettings]):
    defaults: Callable[["Recipe"], RecipeSettings] = lambda self: BaseSettings()  # type: ignore[assignment, return-value]

    def __init__(self, mode: Mode = "machine", settings: RecipeSettings | None = None):
        self.mode = mode
        self.s = settings or self.defaults()
        self.results: list[RecipeResult] = []

    @abstractmethod
    async def execute(self, **kw):
        # To be implemented by the recipe itself
        raise NotImplementedError

    @classmethod
    def slug(cls) -> str:
        """A unique identifier for this recipe, which does not change when the recipe is updated."""
        return cls.__name__.lower()

    def _maybe_add_to_results(self, results: list[RecipeResult] | object):
        if is_list_of_recipe_result(results):
            self.results.extend(results)

    def to_json(self, results: list[RecipeResult] | object) -> list[dict]:
        """Convert results to objects that can be serialized to JSON."""
        if is_list_of_recipe_result(results):
            return [result.dict() for result in results]
        raise NotImplementedError

    async def evaluation_report(self) -> EvaluationReport:
        return EvaluationReport(
            technique_name=str(self),
            results=await map_async(
                self.results, EvaluatedRecipeResult.from_recipe_result
            ),
        )

    def agent(self, agent_name: str | None = None) -> Agent:
        return agent_policy(mode=self.mode, agent_name=agent_name)

    def max_concurrency(self) -> int:
        return 10 if self.mode == "machine" else 1

    def __str__(self) -> str:
        return self.__class__.__name__
