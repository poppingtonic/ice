from typing import Type

from ice.environment import env
from ice.recipe import Recipe
from ice.recipes import get_recipe_classes


async def select_recipe_class(*, recipe_name: str | None = None) -> Type[Recipe]:
    recipe_classes = get_recipe_classes()
    recipe_names = [r.__name__ for r in recipe_classes]
    if recipe_name is not None:
        try:
            recipe_class = next(
                r
                for r in recipe_classes
                if r.__name__.lower().startswith(recipe_name.lower())
            )
        except StopIteration:
            raise ValueError(f"Recipe '{recipe_name}' not found in {recipe_names}")
    else:
        recipe_name = await env().select("Recipe", recipe_names)
        recipe_class = [r for r in recipe_classes if r.__name__ == recipe_name][0]
    return recipe_class
