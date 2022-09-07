#! /usr/bin/env bash

set -eux -o pipefail

START_FRONTEND=false ./scripts/run-local.sh

docker compose exec -- backend python -m main $@ | scripts/open_in_browser.py
