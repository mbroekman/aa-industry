FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Install system dependencies and poetry
RUN apt-get update && apt-get install -y curl libgomp1 && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# Copy poetry files and install dependencies
COPY pyproject.toml ./
RUN poetry install --no-root --only main

# Copy application code
COPY . .

# Run the application
CMD ["uvicorn", "ai_forecasting.main:app", "--host", "0.0.0.0", "--port", "8050"]
