# Stage 1: Build stage
FROM python:3.13-rc-alpine AS build

# Set the working directory
WORKDIR /app

# Install build dependencies, Rust, and Cargo
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    && apk add --no-cache \
    bash \
    git \
    && python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies into the virtual environment
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Final stage
FROM python:3.13-rc-alpine

# Set the working directory
WORKDIR /app

# Copy the virtual environment from the build stage
COPY --from=build /opt/venv /opt/venv

# Copy the stats script
COPY stats_script.py .

# Ensure the virtual environment's binaries are in the PATH
ENV PATH="/opt/venv/bin:$PATH"

# Command to run the stats script
CMD ["python", "stats_script.py"]