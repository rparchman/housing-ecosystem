FROM python:3.11-slim

WORKDIR /app

COPY scheduler/scheduler_service.py /app/scheduler_service.py
COPY scheduler/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "/app/scheduler_service.py"]
