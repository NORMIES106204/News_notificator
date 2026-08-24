# Responsible for: building a one-shot job image that runs a single
# dispatch cycle and exits. Scheduling (when to run this) is handled
# externally by the container orchestrator (cron/k8s CronJob/etc.).
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "src.news_noficicator.main"]