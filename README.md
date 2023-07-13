# Tanks

[![Linting](https://github.com/91nunocosta/tanks/actions/workflows/lint.yml/badge.svg)](https://github.com/91nunocosta/tanks/actions/workflows/lint.yml)
[![Tests](https://github.com/91nunocosta/tanks/actions/workflows/test.yml/badge.svg)](https://github.com/91nunocosta/tanks/actions/workflows/test.yml)
[![Maintainability](https://api.codeclimate.com/v1/badges/edce9d4ddf75589404dc/maintainability)](https://codeclimate.com/github/91nunocosta/tanks/maintainability)

## Trying out

1. Clone the repository:

   ```bash
   git clone git@github.com:91nunocosta/tanks.git
   ```

2. Change to the project directory:

   ```bash
   cd tanks
   ```

3. Run the service locally:

    ```bash
    docker-compose up -d
    ```

4. Open the Open API docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

5. Try out the endpoints (see how [here](https://fastapi.tiangolo.com/#interactive-api-docs-upgrade)).

## Linting and testing

1. Clone the repository.

   ```bash
   git clone git@github.com:91nunocosta/tanks.git
   ```

2. Open the project directory.

   ```bash
   cd tanks
   ```

3. Install [_poetry_](https://python-poetry.org/) _package and dependency manager_.
Follow the [poetry installation guide](https://python-poetry.org/docs/#installation).
Chose the method that is more convenient to you, for example:

   ```bash
   curl -sSL\
        https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py \
      | python -
   ```

4. Create a new virtual environment (managed by _poetry_) with the project dependencies.

   ```bash
   poetry install --with lint --with test --with tox
   ```

5. Enter the virtual environment.

   ```bash
   poetry shell
   ```

6. Run the linters.

    ```bash
    pre-commit run --all-files
    ```

7. Run the tests and measure test coverage.

    ```bash
    tox
    ```
