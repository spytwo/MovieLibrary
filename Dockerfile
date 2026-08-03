FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PIP_ROOT_USER_ACTION=ignore
WORKDIR /app
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root
COPY . .
EXPOSE 8000
CMD ["uvicorn", "movielibrary.main:app", "--host", "0.0.0.0", "--port", "8000"]
