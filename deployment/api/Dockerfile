FROM python:3.11-slim

WORKDIR /app

# Copy application code
COPY api /app/api
COPY pipeline /app/pipeline
COPY deployment/api/gunicorn_conf.py /app/gunicorn_conf.py
COPY deployment/api/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose API port
EXPOSE 8000

# Start API directly with Gunicorn (no nginx)
CMD ["gunicorn", "-c", "gunicorn_conf.py", "api.server:app"]
