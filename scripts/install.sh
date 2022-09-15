#!/usr/bin/env bash
set -eux -o pipefail

export DEBIAN_FRONTEND=noninteractive

apt update
apt install -y software-properties-common

echo 'deb [signed-by=/code/nodesource.gpg] https://deb.nodesource.com/node_16.x focal main' > /etc/apt/sources.list.d/nodesource.list
add-apt-repository ppa:deadsnakes/ppa
apt update
apt install -y \
  build-essential \
  git \
  nodejs \
  python3.10-dev \
  python3.10-venv

npm -g install concurrently
python3.10 -m ensurepip
git config --global --add safe.directory /code

rm -rf /var/lib/apt/lists/*
