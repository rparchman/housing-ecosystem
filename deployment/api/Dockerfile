FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y nginx && apt-get clean

# Copy application code (relative to build context = repo root)
COPY api /app/api
COPY pipeline /app/pipeline
COPY deployment/api/gunicorn_conf.py /app/gunicorn_conf.py
COPY deployment/api/requirements.txt /app/requirements.txt
COPY deployment/api/nginx.conf /etc/nginx/nginx.conf

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose API port
EXPOSE 80

CMD ["bash", "-c", "nginx && gunicorn -c gunicorn_conf.py api.server:app"]
