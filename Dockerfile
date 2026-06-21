# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Set path and working directory
ENV APP_HOME /app
WORKDIR $APP_HOME

# Install system dependencies needed for building certain Python extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy local code to the container image.
COPY . ./

# Install pip dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the web service on container startup.
# Cloud Run sets the PORT environment variable automatically (defaults to 8080)
CMD exec uvicorn api.server:app --host 0.0.0.0 --port ${PORT:-8080}
