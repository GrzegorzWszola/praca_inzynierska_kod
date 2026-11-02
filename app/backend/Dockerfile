FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./backend

RUN useradd -m appuser
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data
USER appuser

EXPOSE 8000
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]