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

# Install the package with uv
RUN uv pip install --system --no-cache -e .

# WebGL backend port
EXPOSE 8766

# Run webgl backend
CMD ["python", "-m", "cube.main_webgl", "--quiet"]
