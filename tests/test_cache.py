import pytest

from pytest_mock import MockerFixture

from ice.apis.openai import openai_complete


@pytest.mark.anyio
async def test_openai_complete_cache(mocker: MockerFixture):

    ret_val = "hello"

    mock_post = mocker.patch("ice.apis.openai._post", return_value=ret_val)

    first_result = await openai_complete("What do you say?")
    assert first_result == ret_val
    mock_post.assert_called_once()

    second_result = await openai_complete("What do you say?")
    assert second_result == ret_val
    mock_post.assert_called_once()

    new_args_result = await openai_complete("New args")
    assert new_args_result == ret_val
    assert mock_post.call_count == 2
