#!/usr/bin/env bash
set -eux -o pipefail

export PIP_DEFAULT_TIMEOUT=100
export PIP_DISABLE_PIP_VERSION_CHECK=on
export PIP_NO_CACHE_DIR=off # Surprisingly, this disables the cache.
export POETRY_VIRTUALENVS_IN_PROJECT=true

pip3.10 install -r poetry-requirements.txt
poetry install --no-interaction --no-ansi --no-cache
