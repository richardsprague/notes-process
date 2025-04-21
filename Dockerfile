# Use a lightweight, secure Python base image (ARM64 compatible)
FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies for Quarto, Pandoc, TinyTeX, Perl, and XeTeX
RUN apt-get update && apt-get install -y \
    curl \
    pandoc \
    wget \
    perl \
    libpod-parser-perl \
    libfontconfig1 \
    fontconfig \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

# Install Quarto CLI for ARM64 (specific version)
RUN curl -L https://github.com/quarto-dev/quarto-cli/releases/download/v1.5.57/quarto-1.5.57-linux-arm64.tar.gz -o quarto.tar.gz \
    && mkdir -p /opt/quarto \
    && tar -xzf quarto.tar.gz -C /opt/quarto --strip-components=1 \
    && ln -s /opt/quarto/bin/quarto /usr/local/bin/quarto \
    && rm quarto.tar.gz

# Install TinyTeX manually with required packages
RUN wget -qO- "https://yihui.org/tinytex/install-unx.sh" | sh \
    && export PATH=/root/.TinyTeX/bin/aarch64-linux:$PATH \
    && /root/.TinyTeX/bin/aarch64-linux/tlmgr path add \
    && /root/.TinyTeX/bin/aarch64-linux/tlmgr install latexmk luatex xetex koma-script tcolorbox tikzfill pdfcol fontawesome5 caption \
    && /root/.TinyTeX/bin/aarch64-linux/tlmgr update --self \
    && /root/.TinyTeX/bin/aarch64-linux/tlmgr path add \
    && mv /root/.TinyTeX /opt/TinyTeX \
    && ln -s /opt/TinyTeX /root/.TinyTeX \
    && ln -s /opt/TinyTeX/bin/aarch64-linux/pdflatex /usr/local/bin/pdflatex \
    && ln -s /opt/TinyTeX/bin/aarch64-linux/latexmk /usr/local/bin/latexmk \
    && ln -s /opt/TinyTeX/bin/aarch64-linux/lualatex /usr/local/bin/lualatex \
    && ln -s /opt/TinyTeX/bin/aarch64-linux/xelatex /usr/local/bin/xelatex \
    && /opt/TinyTeX/bin/aarch64-linux/fmtutil-sys --byengine pdftex --no-error-if-no-format --no-error-if-no-engine=luametatex,luajithbtex,luajittex,mfluajit \
    && /opt/TinyTeX/bin/aarch64-linux/fmtutil-sys --byengine luatex --no-error-if-no-format --no-error-if-no-engine=luametatex,luajithbtex,luajittex,mfluajit \
    && /opt/TinyTeX/bin/aarch64-linux/fmtutil-sys --byengine xetex --no-error-if-no-format --no-error-if-no-engine=luametatex,luajithbtex,luajittex,mfluajit

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create scripts directory (ensure it exists)
RUN mkdir -p /app/scripts

# Copy scripts (if any exist at build time)
COPY scripts/ /app/scripts/

# Command to run your processing script (placeholder, can be overridden)
CMD ["python", "scripts/process_vault.py"]
