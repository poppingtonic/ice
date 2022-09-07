# Interactive Composition Explorer 🧊

Decomposition of paper Q&A using humans and language models

## Table of contents

- [Design principles](#design-principles)
- [Running ICE locally](#running-ice-locally)
  - [Setup](#setup)
  - [Running ICE on the command line](#running-ice-on-the-command-line)
    - [Human data collection](#human-data-collection)
    - [GPT](#gpt)
    - [Cheap tests](#cheap-tests)
  - [Streamlit](#streamlit)
  - [Evaluation](#evaluation)
    - [Evaluate in-app QA results](#evaluate-in-app-qa-results)
    - [Summarize experiment evals](#summarize-experiment-evals)
- [Development](#development)
  - [Adding new Python dependencies](#adding-new-python-dependencies)
  - [Changing the database schema](#changing-the-database-schema)
  - [Regenerating the TypeScript definitions](#regenerating-the-typescript-definitions)
  - [Contributions](#contributions)
- [Web app deployment](#web-app-deployment)
  - [Running the web app locally](#running-the-web-app-locally)
  - [Running previews of the app for PRs](#running-previews-of-the-app-for-prs)
  - [Running the web app in production](#running-the-web-app-in-production)
  - [Connecting to the database](#connecting-to-the-database)
    - [Navigating the database](#navigating-the-database)

## Design principles

- **Recipes** are decompositions of a task into subtasks.

  The meaning of a recipe is: If a human executed these steps and did a good job at each workspace in isolation, the overall answer would be good. This decomposition may be informed by what we think ML can do at this point, but the recipe itself (as an abstraction) doesn’t know about specific agents.

  Recipes are executed lazily by the `ExecutionDAG` available on the recipe's `build_dag` method as `self.dag`. In particular, the `self.dag.register` decorator method converts an eager function that accepts nodes and returns a value into a lazy function to be executed when needed as the graph is run. The return value of this decorated function is a `Node`, which can itself be passed to other nodes.

- **Nodes** are subtasks that can perform arbitrary computation on nodes to return a value.

  Nodes are the primary building blocks of recipes. When constructing a recipe, you get nodes by calling functions that themselves are `self.dag.register` decorated functions that accept zero or more nodes as keyword arguments.

  In order to ask for inputs from humans or models, `Node` functions should ask an agent via `self.dag.agent()` methods such as `answer` (completion) or `score` (probability assignment).

- **Agents** perform atomic subtasks of predefined shapes, like completion, scoring, or classification.

  Agents don't know which recipe is calling them. Agents don’t maintain state between subtasks. Agents generally try to complete all subtasks they're asked to complete (however badly), but some will not have implementations for certain task types.

- The **mode** in which a recipe runs is a global setting that can affect every agent call. For instance, whether to use humans or agents. Recipes can also run with certain `RecipeSettings`, which can map a task type to a specific `agent_name`, which can modify which agent is used for that specfic type of task.

## Running ICE locally

### Setup

1. Add required secrets to `.env`:

   ```sh
   echo 'OPENAI_API_KEY="sk-Aes1...L"' >> .env
   echo 'OPENAI_ORG_ID="org-5p0N...X"' >> .env
   echo 'OUGHT_INFERENCE_API_KEY="fe7...6"' >> .env
   echo 'NEXT_PUBLIC_API_HOST="http://localhost:8000"' >> ui/.env
   ```

1. Build the container:

   ```sh
   docker compose build
   ```

1. Run the services:

   ```sh
   docker compose up
   ```

1. If you've used ICE before, migrate the database:

   ```sh
   docker compose exec backend alembic upgrade head
   ```

### Setup for Anthropic models

To use anthropic models (agents), you must add a valid `ANTHROPIC_API_KEY` to your environment.

1. Ask Ben Mann to authorize your GitHub account via the Anthropic slack channel.

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
./scripts/run-cli.sh -m human
```

Human with GPT default completions:

```sh
./scripts/run-cli.sh -m augmented
```

#### GPT

```sh
./scripts/run-cli.sh -m machine
```

You can run on the iteration gold standards of a specific recipe like

```sh
./scripts/run-cli.sh -m machine -r placebotree -q placebo -g iterate
```

To run over multiple gold standard splits, just provide them separated by spaces:

```sh
scripts/run-cli.sh -m machine -r placebotree -q placebo -g iterate validation
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

#### Summarize experiment evals

You can run a recipe, update and evaluate the results by hand, then summarize those evaluations:

1. [Run a recipe](#gpt)
2. Upload the per-experiments results from `data/evaluation_csvs/experiments_evaluation...` to [the eval Airtable](https://airtable.com/app4Fo26j2vGYufCe/tblc9Ujp0bQ3XpzMw/viwzNlDfvxbQFcHCb?blocks=bipfL0jXEg7yg8pQC) using the CSV import extension, evaluate them, and download the result as a CSV
3. Run `./scripts/summarize_experiment_evals <PATH_TO_EVAL_RESULT_CSV>`. This will:
   1. evaluate and summarize classifications
   2. summarize answer ratings

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
./scripts/run-cli.sh -m test
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

### Changing the database schema

We use [Alembic](https://alembic.sqlalchemy.org/) to manage the database schema.

1. Change the model definitions in `database.py`.
2. Generate the migrations:
   ```sh
   docker compose exec backend alembic revision --autogenerate -m "human-readable description here"
   ```
3. Check and edit the newly-created file in `migrations/versions`. You will often need to customise the details of how columns are created.
4. To run the migration locally:
   ```sh
   docker compose exec backend alembic upgrade head
   ```
5. Your PR will run the migration in the dev database automatically (see `release_command` in `fly.toml`)
6. When your PR is merged to `main` and deployed, the migration will be run automatically in the prod database by the same mechanism

### Regenerating the TypeScript definitions

We can generate type definitions for TypeScript using the automatically-generated OpenAPI spec from FastAPI. If you have created or updated models used in API definitions, run:

```sh
./scripts/generate-ts-models.sh
```

### Contributions

Before making a PR, check linting, types, tests, etc:

```sh
scripts/checks.sh
```

## Web app

### Running the web app locally

The web app consists of a [FastAPI](https://fastapi.tiangolo.com/) back-end and a [Next.js](https://nextjs.org/) front-end.

Use the `run-local.sh` script as so:

```sh
./scripts/run-local.sh
```

This uses `docker compose` to run the app server, and `npm` to run a development version of the Next front-end.

You can access the front-end on <http://localhost:3000/workspace>, and if you need to, the back-end on <http://localhost:8000/>.

### Running previews of the app for PRs

When you create a PR, a preview app for the backend and frontend are automatically deployed.

You can see the links to these apps in the deployment comment of the PR:

_TODO_: screenshot

We share a single Postgres server (`dev-ice-db`) between all the preview apps, but each preview gets its own database namespace.

### Running the web app in production

The back-end is running in [Fly.io](https://fly.io/apps/ice); the front-end is in [Vercel](https://vercel.com/ought/ice).

**TODO** add information about how production deploys are updated

### Connecting to the database

You have two options to view the data in your database:

1. **Simpler**: connect via the `fly postgres connect` command (details below)
1. **More powerful**: Connect your own Postgres client via port forwarding (details)

`fly postgres connect` gives you a conventional `psql` interface:

```
> fly postgres connect -a dev-ice-db
WARN app flag 'dev-ice-db' does not match app name in config file 'ice'
? Continue using 'dev-ice-db' Yes
Connecting to dev-ice-db.internal... complete
psql (14.2 (Debian 14.2-1.pgdg110+1))
Type "help" for help.

postgres=#
```

Alternatively you can forward a local port to your Postgres server (e.g. if you want to use a better Postgres client app):

```
> flyctl proxy 5432:5432 -a dev-ice-db
Update available 0.0.328 -> v0.0.330.
Run "flyctl version update" to upgrade.
Proxying local port 5432 to remote [dev-ice-db.internal]:5432

```

For **dev-ice-db** you can get the connection secrets [here in 1Password](https://start.1password.com/open/i?a=GEF4ZCJ275HSXH5AV2PUCOVO4Q&v=7osu4kqyoy3gekmyaghjiqbvne&i=e2udby275betxf5lwe44atkpgy&h=ought.1password.com).

#### Navigating the database

Whether you connect directly or via a port forward, in staging the app name for the Postgres server is `dev-ice-db`; in production it is `prod-ice-db`.

```
postgres=# \l
                                        List of databases
       Name        |   Owner    | Encoding |  Collate   |   Ctype    |     Access privileges
-------------------+------------+----------+------------+------------+---------------------------
 ice_pr_11_backend | flypgadmin | UTF8     | en_US.utf8 | en_US.utf8 |
 ice_pr_12_backend | flypgadmin | UTF8     | en_US.utf8 | en_US.utf8 |
 ice_pr_13_backend | flypgadmin | UTF8     | en_US.utf8 | en_US.utf8 |
 ice_pr_14_backend | flypgadmin | UTF8     | en_US.utf8 | en_US.utf8 |
 ice_pr_15_backend | flypgadmin | UTF8     | en_US.utf8 | en_US.utf8 |
 ice_pr_6_backend  | flypgadmin | UTF8     | en_US.utf8 | en_US.utf8 |
 ice_pr_7_backend  | flypgadmin | UTF8     | en_US.utf8 | en_US.utf8 |
 postgres          | flypgadmin | UTF8     | en_US.utf8 | en_US.utf8 |
 pr_11_null_null   | flypgadmin | UTF8     | en_US.utf8 | en_US.utf8 |
 template0         | flypgadmin | UTF8     | en_US.utf8 | en_US.utf8 | =c/flypgadmin            +
                   |            |          |            |            | flypgadmin=CTc/flypgadmin
 template1         | flypgadmin | UTF8     | en_US.utf8 | en_US.utf8 | =c/flypgadmin            +
                   |            |          |            |            | flypgadmin=CTc/flypgadmin

ice_pr_6_backend=# \c ice_pr_7_backend
You are now connected to database "ice_pr_7_backend" as user "postgres".
ice_pr_7_backend=# \d
                    List of relations
 Schema |       Name        |   Type   |      Owner
--------+-------------------+----------+------------------
 public | alembic_version   | table    | ice_pr_7_backend
 public | completion        | table    | ice_pr_7_backend
 public | completion_id_seq | sequence | ice_pr_7_backend
(3 rows)
ice_pr_7_backend=# select id, document_id, excerpt_hash from completion order by id desc limit 5;

 id |   document_id    |           excerpt_hash
----+------------------+----------------------------------
  7 | abebe-2018.pdf   | b6a2d07a2b2b2274d6a92798555a025e
  6 | abebe-2018.pdf   | b6a2d07a2b2b2274d6a92798555a025e
  5 | abebe-2018.pdf   | b6a2d07a2b2b2274d6a92798555a025e
  4 | abebe-2018.pdf   | b6a2d07a2b2b2274d6a92798555a025e
  3 | Hibbeln-2018.pdf | ec7eec434df24b9c4438be4b2881280b
(5 rows)
```
