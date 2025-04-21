# Notes Process Makefile
# Usage: make <target>

.PHONY: clean process render build

clean:
	@echo "Cleaning output directory..."
	@rm -rf output

process: clean
	@echo "Processing markdown files..."
	@docker run --rm -v $(PWD):/app -it notes-process python scripts/process_vault.py

render:
	@echo "Rendering Quarto project..."
	@docker run --rm -v $(PWD):/app -it notes-process quarto render /app/output

build:
	@echo "Building Docker image..."
	@docker build -t notes-process .