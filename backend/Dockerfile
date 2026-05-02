# Google Services: Cloud Run deployment container
# Efficiency: Slim base image for fast cold starts
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
# Efficiency: Upgrade pip to avoid legacy resolver issues
RUN pip install --upgrade pip
# Google Services: Install all Google Cloud SDK dependencies
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Security: Non-root user for container hardening
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser
ENV PORT=8080
EXPOSE 8080
# Google Services: Cloud Run requires listening on $PORT
CMD uvicorn main:app --host 0.0.0.0 --port $PORT