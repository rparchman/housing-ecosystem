FROM python:3.11-slim

WORKDIR /app

# Copy scheduler service
COPY scheduler/scheduler_service.py /app/scheduler_service.py

# Copy pipeline directory
COPY pipeline /app/pipeline

# Copy requirements
COPY scheduler/requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "scheduler_service.py"]
