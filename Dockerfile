
# Use a lightweight, secure Python base image (ARM64 compatible)
FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies for Quarto and markdown processing
RUN apt-get update && apt-get install -y \
    curl \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

# Install Quarto CLI for ARM64 (specific version)
RUN curl -L https://github.com/quarto-dev/quarto-cli/releases/download/v1.5.57/quarto-1.5.57-linux-arm64.tar.gz -o quarto.tar.gz \
    && mkdir -p /opt/quarto \
    && tar -xzf quarto.tar.gz -C /opt/quarto --strip-components=1 \
    && ln -s /opt/quarto/bin/quarto /usr/local/bin/quarto \
    && rm quarto.tar.gz

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your processing scripts
COPY scripts/ ./scripts/

# Command to run your processing script (placeholder, can be overridden)
CMD ["python", "scripts/process_vault.py"]