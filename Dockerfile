# Stage 1: Build frontend with Vite
FROM node:20-slim AS frontend-build
WORKDIR /build
COPY src/cube/presentation/gui/backends/webgl/package.json \
     src/cube/presentation/gui/backends/webgl/package-lock.json ./
RUN npm ci
COPY src/cube/presentation/gui/backends/webgl/vite.config.js ./
COPY src/cube/presentation/gui/backends/webgl/static/ static/
RUN npx vite build

# Stage 2: Python runtime
FROM python:3.14-slim

WORKDIR /app

# Ensure Python output appears in fly logs (no buffering in containers)
ENV PYTHONUNBUFFERED=1

# Install system deps for numpy/kociemba build + uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Copy Vite build output over source static files
COPY --from=frontend-build /build/static/dist/ src/cube/presentation/gui/backends/webgl/static/dist/

# Install the package with uv
RUN uv pip install --system --no-cache -e .

# WebGL backend port
EXPOSE 8766

# Run webgl backend
CMD ["python", "-m", "cube.main_webgl", "--quiet"]
