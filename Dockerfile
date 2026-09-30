# Responsible for: building a one-shot job image that runs a single
# dispatch cycle and exits. Scheduling (when to run this) is handled
# externally by the container orchestrator (cron/k8s CronJob/etc.).
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY src/ ./src
COPY config/ ./config
COPY tests/ ./tests
CMD ["python", "-m", "src.news_notificator.main"]