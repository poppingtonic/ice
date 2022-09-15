FROM nvidia/cuda:11.6.1-runtime-ubuntu20.04
WORKDIR /code

COPY nodesource.gpg ./
COPY scripts/install.sh scripts/
RUN scripts/install.sh

COPY poetry-requirements.txt poetry.lock pyproject.toml ./
COPY scripts/install-poetry.sh scripts/
RUN scripts/install-poetry.sh

ENV \
  PRE_COMMIT_HOME=.pre-commit-home \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  VIRTUAL_ENV=/code/.venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN python -c "import nltk; nltk.download('punkt')"

COPY ui/package*.json ui/
RUN (cd ui && npm ci)

COPY . .

CMD ["concurrently", "sleep infinity", "cd ui && npm run dev"]
