#############################
# STAGE 1: Install Deps     #
#############################
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Preinstall build tools and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    pkg-config \
    libcairo2-dev \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

#####################################
# STAGE 2: Production Runtime Only  #
#####################################
FROM python:3.11-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies (PostgreSQL client)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage
COPY --from=builder /install /usr/local

# Copy project files into the production container
COPY manage.py ./
COPY config/ ./config/
COPY apps/ ./apps/

# Optional: expose both ports (if you're running your app on 8000)
EXPOSE 8000

# Optionally set the entrypoint and command (if you want to run gunicorn directly)
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
