FROM python:3.14-slim

WORKDIR /app

# Install system deps for numpy/kociemba build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Upgrade pip, then install the package
RUN python -m pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -e .

# Web backend port
EXPOSE 8765

# Run web backend
CMD ["python", "-m", "cube.main_web", "--quiet"]
