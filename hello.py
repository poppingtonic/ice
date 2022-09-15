from ice.recipe import recipe


async def foo():
    return "bar"


@recipe.main
async def say_hello():
    await foo()
    return "Hello world!"
