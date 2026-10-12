# app/book-parser/Dockerfile
FROM python:3.12-slim
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir ".[test]"

COPY tests/ ./tests/
CMD ["pytest", "-v", "--cov=ml_engine", "tests/"]