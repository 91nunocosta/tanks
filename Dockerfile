FROM python:3.11

WORKDIR /app

RUN pip install poetry

COPY ./pyproject.toml ./pyproject.toml
COPY ./poetry.lock ./poetry.lock

RUN poetry config virtualenvs.create false \
  && poetry export -f requirements.txt > requirements.txt \
  && pip install --no-cache-dir -r requirements.txt \
  && rm requirements.txt

COPY ./tanks ./tanks

CMD uvicorn --host=${HOST} --port=${PORT} --factory tanks.main:create_app
