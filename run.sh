
#!/bin/bash

# Notes Process Runner
# Usage: ./run.sh [process|render|build]

set -e

case "$1" in
  process)
    echo "Processing markdown files..."
    docker run --rm -v "$(pwd)":/app -it notes-process python scripts/process_vault.py
    ;;
  render)
    echo "Rendering Quarto project..."
    docker run --rm -v "$(pwd)":/app -it notes-process quarto render /app/output
    ;;
  build)
    echo "Building Docker image..."
    docker build -t notes-process .
    ;;
  *)
    echo "Usage: $0 [process|render|build]"
    echo "  process: Process Obsidian markdown files into a Quarto project"
    echo "  render: Render Quarto project to HTML, PDF, and EPUB"
    echo "  build: Build the notes-process Docker image"
    exit 1
    ;;
esac
