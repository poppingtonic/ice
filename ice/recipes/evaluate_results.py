from structlog.stdlib import get_logger

from ice.recipe import Recipe
from ice.recipes.evaluate_result import EvaluateResult
from ice.recipes.evaluate_result import ResultComparison
from ice.utils import map_async

log = get_logger()


class EvaluateResults(Recipe):
    name = "EvaluateResults"

    async def execute(self, **kw) -> list[ResultComparison]:
        """
        Compare two lists of results, model and gold standard.
        """
        model_results: list[str]
        gold_results: list[str]
        question: str

        evaluate_result = EvaluateResult(mode=self.mode)

        if not kw.get("model_results") and not kw.get("gold_results"):
            if not self.mode == "test":
                log.warning("No model results and no gold results - using test data.")
            model_results, gold_results, question = evaluate_result.test_data(n=3)
        else:
            model_results = kw["model_results"]
            gold_results = kw["gold_results"]
            question = kw["question"]

        comparisons = await map_async(
            list(zip(model_results, gold_results)),
            lambda pair: evaluate_result.execute(
                question=question, model_result=pair[0], gold_result=pair[1]
            ),
            max_concurrency=self.max_concurrency(),
            show_progress_bar=True,
        )

        return comparisons
