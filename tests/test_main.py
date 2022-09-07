from typing import Type

import nest_asyncio
import pytest

from ice.recipe import Recipe
from ice.recipes import get_recipe_classes
from main import main_cli


nest_asyncio.apply()


def do_not_test(recipe: Type[Recipe]) -> bool:
    if hasattr(recipe, "do_not_test"):
        return recipe.do_not_test  # type: ignore
    return False


@pytest.mark.parametrize(
    "recipe_name",
    [recipe.name for recipe in get_recipe_classes() if not do_not_test(recipe)],
)
@pytest.mark.anyio
async def test_recipes(recipe_name: str):
    main_cli(
        mode="test",
        input_files=["./papers/keenan-2018-tiny.txt"],
        recipe_name=recipe_name,
    )
