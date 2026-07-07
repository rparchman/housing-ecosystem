FROM python:3.11-slim

WORKDIR /app

COPY scheduler/scheduler_service.py /app/scheduler_service.py
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "scheduler_service.py"]
