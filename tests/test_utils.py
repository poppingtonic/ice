import pytest

from anyio import sleep

from ice.utils import nsmallest_async
from ice.utils import ProactiveRateLimitError
from ice.utils import token_bucket


async def cmp(x: int, y: int) -> int:
    return x - y


@pytest.mark.anyio
async def test_nsmallest_async():
    xs = [7, 8, 4, 3, 1, 6, 2, 0, 9, 5]
    assert await nsmallest_async(3, xs, cmp) == [0, 1, 2]
    assert xs == [7, 8, 4, 3, 1, 6, 2, 0, 9, 5]

    assert await nsmallest_async(1, [], cmp) == []
    assert await nsmallest_async(0, [1], cmp) == []
    assert await nsmallest_async(1, [2, 1, 3], cmp) == [1]
    assert await nsmallest_async(-1, [2, 1, 3], cmp) == []
    assert await nsmallest_async(4, [2, 1, 3], cmp) == [1, 2, 3]
    assert await nsmallest_async(1, [1], cmp) == [1]
    assert await nsmallest_async(3, list(range(10)), cmp) == [0, 1, 2]


@pytest.mark.anyio
async def test_token_bucket_normal():
    @token_bucket(3, 10)
    async def add_one(x):
        return x + 1

    assert await add_one(1) == 2
    assert await add_one(2) == 3
    assert await add_one(3) == 4


@pytest.mark.anyio
async def test_token_bucket_exception():
    @token_bucket(3, 10)
    async def add_one(x):
        return x + 1

    await add_one(1)
    await add_one(2)
    await add_one(3)
    with pytest.raises(ProactiveRateLimitError):
        await add_one(4)


@pytest.mark.slow
@pytest.mark.anyio
async def test_token_bucket_wait():
    @token_bucket(3, 10)
    async def add_one(x):
        return x + 1

    await add_one(1)
    await add_one(2)
    await add_one(3)
    await sleep(5)
    assert await add_one(4) == 5
