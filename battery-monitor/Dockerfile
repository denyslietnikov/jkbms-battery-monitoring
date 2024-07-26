# Stage 1: Build stage
FROM python:3.13-rc-alpine AS builder

# Install necessary build packages
RUN apk add --no-cache \
    cargo \
    build-base \
    libffi-dev \
    openssl-dev \
    bluez-dev \
    linux-headers \
    glib-dev \
    bash

# Set working directory
WORKDIR /app

# Copy project files to the container
COPY . .

# Create virtual environment and install Python dependencies
RUN python3 -m venv /app/jkbms-monitoring && \
    /app/jkbms-monitoring/bin/pip install --no-cache-dir --upgrade pip wheel && \
    /app/jkbms-monitoring/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.13-rc-alpine

# Install necessary runtime packages
RUN apk add --no-cache \
    bluez \
    glib

# Set working directory
WORKDIR /app

# Copy virtual environment from the build stage
COPY --from=builder /app/jkbms-monitoring /app/jkbms-monitoring

# Copy project files to the container
COPY . .

# Ensure the virtual environment's binaries are in the PATH
ENV PATH="/app/jkbms-monitoring/bin:$PATH"

# Command to run the script
CMD ["python", "monitor.py"]