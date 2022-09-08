# Interactive Composition Explorer 🧊

Decomposition of paper Q&A using humans and language models

## Table of contents

- [Design principles](#design-principles)
- [Running ICE with codespaces](#running-ice-with-codespaces)
- [Running ICE locally](#running-ice-locally)
  - [Requirements](#requirements)
  - [Setup](#setup)
  - [Running ICE on the command line](#running-ice-on-the-command-line)
    - [Human data collection](#human-data-collection)
    - [GPT](#gpt)
  - [Streamlit](#streamlit)
  - [Evaluation](#evaluation)
  - [Evaluate in-app QA results](#evaluate-in-app-qa-results)
- [Development](#development)
  - [Adding new Python dependencies](#adding-new-python-dependencies)
  - [Contributions](#contributions)

## Design principles

- **Recipes** are decompositions of a task into subtasks.

  The meaning of a recipe is: If a human executed these steps and did a good job at each workspace in isolation, the overall answer would be good. This decomposition may be informed by what we think ML can do at this point, but the recipe itself (as an abstraction) doesn’t know about specific agents.

- **Agents** perform atomic subtasks of predefined shapes, like completion, scoring, or classification.

  Agents don't know which recipe is calling them. Agents don’t maintain state between subtasks. Agents generally try to complete all subtasks they're asked to complete (however badly), but some will not have implementations for certain task types.

- The **mode** in which a recipe runs is a global setting that can affect every agent call. For instance, whether to use humans or agents. Recipes can also run with certain `RecipeSettings`, which can map a task type to a specific `agent_name`, which can modify which agent is used for that specfic type of task.

## Running ICE with Codespaces

A convenient way to develop ICE is to use GitHub codespaces.

1. Increase the default idle timeout in [your settings](https://github.com/settings/codespaces#default-idle-timeout-header) from 30 minutes to a few hours.
2. Go [here](https://github.com/oughtinc/ice9/codespaces) to create a new codespace.
3. The development requirements are already installed in the codespace, so you don't need to install Docker or Node. Follow the [setup instructions](#setup) as usual.
4. To share your visualizations publicly, on the ports pane, change port 3000 to be public, and click the 🌐 icon to get the link.

## Running ICE locally

### Requirements

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) to run the containerized python application.
2. Node to run the composition visualization tool. Node can be installed via [nvm](https://github.com/nvm-sh/nvm). Install `nvm`, then `cd ui && nvm use && npm install`.

### Setup

1. Add required secrets to `.env`:

   ```sh
   echo 'OPENAI_API_KEY="sk-Aes1...L"' >> .env
   echo 'OPENAI_ORG_ID="org-5p0N...X"' >> .env
   echo 'OUGHT_INFERENCE_API_KEY="fe7...6"' >> .env
   ```

1. If running for the first time, install the visualization dependencies:

   ```sh
   (cd ui; npm ci)
   ```

1. Start the python application and the visualization tool:

   ```sh
   ./scripts/run-local.sh
   ```

### Setup for Anthropic models

To use anthropic models (agents), you must add a valid `ANTHROPIC_API_KEY` to your environment.

1. Ask @stuhlmueller to authorize your GitHub account.

2. Retrieve an auth token from GitHub:

   ```sh
   brew install yq gh
   gh auth login -s user:email  # If asked to reauthenticate, answer yes
   # Whenever you need a new token
   TOKEN=$(cat /Users/$USER/.config/gh/hosts.yml | yq '.["github.com"] | (.user + ":" + .oauth_token)' | tr -d '\n' | base64)
   echo "ANTHROPIC_API_KEY=$TOKEN" >> .env
   ```

3. Then restart the container.

### Running ICE on the command line

#### Human data collection

Human without GPT default completions:

```sh
./scripts/run-recipe.sh -m human
```

Human with GPT default completions:

```sh
./scripts/run-recipe.sh -m augmented
```

#### GPT

```sh
./scripts/run-recipe.sh -m machine
```

You can run on the iteration gold standards of a specific recipe like

```sh
./scripts/run-recipe.sh -m machine -r placebotree -q placebo -g iterate
```

To run over multiple gold standard splits, just provide them separated by spaces:

```sh
scripts/run-recipe.sh -m machine -r placebotree -q placebo -g iterate validation
```

### Streamlit

Run the streamlit apps like this:

```sh
./scripts/run-streamlit.sh
```

This opens a multi-page app that lets you select specific scripts.

To add a page, simply create a script in the `streamlits/pages` folder.

### Evaluation

When you run a recipe, ICE will evaluate the results based on the gold standards in `gold_standards/`. You'll see the results on-screen, and they'll be saved as CSVs in `data/evaluation_csvs/`. You can then upload the CSVs to the "Performance dashboard" and "Individual paper eval" tables in the [ICE Airtable](https://airtable.com/app4Fo26j2vGYufCe/tblkFq839UrBrj9P9/viwDkUqYMQtDAl773?blocks=hide).

#### Evaluate in-app QA results

1. Set up both `ice` and `elicit-next` so that they can run on your computer
2. Switch to the `eval` branch of `elicit-next`, or a branch from the eval branch. This branch should contain the QA code and gold standards that you want to evaluate.
3. If the `ice` QA gold standards (`gold_standards/gold_standards.csv`) may not be up-to-date, download [this Airtable view](https://airtable.com/app4Fo26j2vGYufCe/tbl0JN0LFtDi5SrS5/viws799VwN4AXMNii?blocks=hide) (all rows, all fields) as a CSV and save it as `gold_standards/gold_standards.csv`
4. Duplicate the [All rows, all fields](https://airtable.com/app4Fo26j2vGYufCe/tbl0JN0LFtDi5SrS5/viws799VwN4AXMNii?blocks=hide) view in Airtable, then in your duplicated view, filter to exactly the gold standards you'd like to evaluate and download it as a CSV. Save that CSV as `api/eval/gold_standards/gold_standards.csv` in `elicit-next`
5. Make sure `api/eval/papers` in `elicit-next` contains all of the gold standard papers you want to evaluate
6. In `ice`, run `scripts/eval-in-app-qa.sh <path to elicit-next>`. If you have `elicit-next` cloned as a sibling of `ice`, this would be `scripts/eval-in-app-qa.sh $(pwd)/../elicit-next/`.

This will generate the same sort of eval as for ICE recipes.

## Development

### Running tests

Cheap integration tests:

```sh
./scripts/run-recipe.sh -m test
```

Unit tests:

```sh
./scripts/run-tests.sh
```

### Adding new Python dependencies

1. Manually add the dependency to `pyproject.toml`
2. Update the lock file and install the changes:

```sh
docker compose exec backend poetry lock --no-update
docker compose exec backend poetry install
```

The lockfile update step will take about 15 minutes.

You **do not** need to stop, rebuild, and restart the docker containers.

### Upgrading poetry

To upgrade poetry to a new version:

1. In the Dockerfile, temporarily change `pip install -r poetry-requirements.txt` to `pip install poetry==DESIRED_VERSION`
2. Generate a new `poetry-requirements.txt`:
   ```sh
   docker compose build
   docker compose up -d
   docker compose exec backend bash -c 'pip freeze > poetry-requirements.txt'
   ```
3. Revert the Dockerfile changes

### Contributions

Before making a PR, check linting, types, tests, etc:

```sh
scripts/checks.sh
```
