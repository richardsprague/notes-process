# Notes Process

This project processes markdown files exported from an Obsidian vault (e.g., `~/vaults/notes`, `~/vaults/archive`) into a Quarto book, generating HTML, PDF, and EPUB outputs. It uses Python for preprocessing, Docker for a consistent environment, and TinyTeX for PDF rendering. The workflow is designed for macOS (tested on M2) with VS Code and Git.

## Purpose

- **Input**: Markdown files exported from Obsidian, organized in subfolders (e.g., `input/Notes 2025Q1/`), with images in `input/_resources/`.
- **Processing**: Converts `.md` files to `.qmd` in `output/`, copies referenced images to `output/_resources/`, fixes image paths to `_resources/`, and concatenates daily notes (`Notes YYMMDD*` with `tag: notes`) into `output/Notes-All.qmd`.
- **Rendering**: Uses a manually maintained `_quarto.yml` in the project root to render `output/*.qmd` to `docs/` as HTML, PDF, and EPUB.
- **Output**: A book with HTML (`docs/index.html`), PDF (`docs/book.pdf`), and EPUB (`docs/book.epub`) formats.

## Prerequisites

- **macOS**: Tested on M2 (ARM64).
- **Docker**: For running the processing and rendering environment.
- **VS Code**: For editing, Git integration, and running tasks.
- **Git**: For version control.
- **Obsidian**: With the `markdown export` plugin to export vaults to `input/`.
- **Internet**: For initial Docker build (pulls `python:3.13-slim-bookworm`, Quarto, TinyTeX).

## Folder Structure

```
notes-process/
├── _quarto.yml         # Quarto configuration for rendering output/ to docs/
├── Dockerfile          # Defines the Docker image with Python, Quarto, TinyTeX
├── requirements.txt    # Python dependencies (pyyaml, markdown, python-dateutil)
├── scripts/
│   └── process-vault.py  # Script to convert .md to .qmd and copy images
├── input/              # Exported Obsidian markdown files (ignored by Git)
│   ├── _resources/     # Images referenced in markdown
│   ├── Notes 2025Q1/   # Example subfolder with .md files
│   └── ...
├── output/             # Processed .qmd files and images (ignored by Git)
│   ├── _resources/     # Copied images referenced in .qmd files
│   ├── index.qmd       # Book index
│   ├── Notes-All.qmd   # Concatenated daily notes
│   ├── *.qmd           # Other processed chapters
├── docs/               # Rendered outputs (ignored by Git)
│   ├── _resources/     # Images copied by Quarto
│   ├── index.html      # HTML output
│   ├── book.pdf        # PDF output
│   ├── book.epub       # EPUB output
├── .vscode/
│   ├── tasks.json      # VS Code tasks for processing and rendering
│   ├── launch.json     # VS Code debug configurations for Run and Debug menu
├── run.sh              # Shell script for terminal shortcuts
├── Makefile            # Makefile for terminal-based build tasks
├── .gitignore          # Ignores input/, output/, docs/, .vscode/, *.code-workspace
└── README.md           # This file
```

## Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/richardsprague/notes-process.git
   cd notes-process
   ```

2. **Install Docker**:
   - Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/) for macOS.
   - Start Docker and ensure it’s running.

3. **Export Obsidian Vault**:
   - In Obsidian, use the `markdown export` plugin to export your vault (e.g., `~/vaults/notes`) to `~/dev/notes/notes-process/input/`.
   - Ensure images are in `input/_resources/` and markdown files are in subfolders (e.g., `input/Notes 2025Q1/`).
   - Example `.md` file:
     ```markdown
     # File: input/Notes 2025Q1/Notes 250413 Sunday.md
     ---
     created: 2025-04-13 06:04
     tags:
       - notes
     ---
     Our Walmart delivery arrived today...
     ![](_resources/935414628fc97270bb7b35424032f850.jpg)
     ```

4. **Build the Docker Image**:
   ```bash
   docker build -t notes-process .
   ```
   - Installs Python, Quarto (1.5.57), TinyTeX, and LaTeX packages (`koma-script`, `tcolorbox`, etc.) for rendering.

## Usage

### Step 1: Process Markdown Files
Run `process-vault.py` to convert `input/*.md` to `output/*.qmd` and copy referenced images to `output/_resources/`.

#### Option 1: Via VS Code Run and Debug Menu
1. Open `~/dev/notes/notes-process` in VS Code.
2. Open the **Run and Debug** panel (`Cmd + Shift + D` or click the play/debug icon).
3. Select `Process Notes` from the dropdown.
4. Click the green play button or press `F5`.
5. Output appears in the integrated terminal.

#### Option 2: Via VS Code Tasks
1. Open `~/dev/notes/notes-process` in VS Code.
2. Open the Command Palette (`Cmd + Shift + P`).
3. Select `Tasks: Run Task` and choose `Process Notes`.
4. Or press `Cmd + Shift + B` (default build task).

#### Option 3: Via Makefile
```bash
make process
```
- Runs `clean` (removes `output/` including hidden files like `.quarto`) and `process-vault.py`.

#### Option 4: Via Terminal
```bash
docker run --rm -v ~/dev/notes/notes-process:/app -it notes-process python scripts/process-vault.py
```

**Output**:
- `output/` contains `.qmd` files (e.g., `index.qmd`, `Notes-All.qmd`, `Martha_2025.qmd`) and `_resources/` with referenced images.
- Example `output/Martha_2025.qmd`:
  ```markdown
  ---
  created: 2025-01-13 05:40
  tags:
  - martha
  - notes
  ---
  235 W 63RD ST PH PA
  New York, NY 10023
  From January 8 or so, she’s been terribly ill...
  ![](_resources/349fe6a1a53ce966bcde781704c088d2.jpeg)
  ```
- Example `output/Notes-All.qmd`:
  ```markdown
  # All Notes
  <div class="raw"><p class="date-box">Wednesday, April 02</p></div>
  Our guide Tiffany met us at our hotel...
  ![](_resources/935414628fc97270bb7b35424032f850.jpg)
  **South Kaibab Trail**
  ...
  ```

### Step 2: Render Quarto Project
Use `_quarto.yml` in `notes-process/` to render `output/*.qmd` to `docs/`.

#### Option 1: Via VS Code Run and Debug Menu
1. Open the **Run and Debug** panel (`Cmd + Shift + D`).
2. Select `Render Quarto` from the dropdown.
3. Click the green play button or press `F5`.

#### Option 2: Via VS Code Tasks
1. Open the Command Palette (`Cmd + Shift + P`).
2. Select `Tasks: Run Task` and choose `Render Quarto`.

#### Option 3: Via Makefile
```bash
make render
```

#### Option 4: Via Terminal
```bash
docker run --rm -v $(pwd):/app -it notes-process quarto render /app/output
```

**Output**:
- `docs/` contains:
  ```
  docs/
  ├── _resources/
  │   ├── 935414628fc97270bb7b35424032f850.jpg
  │   ├── 349fe6a1a53ce966bcde781704c088d2.jpeg
  │   ├── ...
  ├── index.html
  ├── Notes-All.html
  ├── Martha_2025.html
  ├── Leah_2025.html
  ├── Martha_Concert_2025-04-13.html
  ├── book.pdf
  ├── book.epub
  ```

### View Outputs
- Open `docs/index.html` in a browser, `docs/book.pdf` in a PDF viewer, or `docs/book.epub` in an e-reader.
- Check `output/*.qmd` for processed content.

## Troubleshooting

- **Image Rendering Issues**:
  - Ensure images exist in `input/_resources/` (e.g., `935414628fc97270bb7b35424032f850.jpg`).
  - Verify `output/_resources/` and `docs/_resources/` contain referenced images after processing and rendering.
  - Check `.qmd` files for correct paths (`![](_resources/image.jpg)`).
  - Share a sample `.md` file with image links to debug.

- **Link Warnings**:
  - Warnings like `Unable to resolve link target: Collateral (2018).md` indicate missing or mismatched `.md` files in `input/`.
  - Run:
    ```bash
    find ~/dev/notes/notes-process/input -name "*.md" | grep -i "Collateral\|Martha\|Leah"
    ```
  - Share `.md` snippets from `Notes 250417 Thursday.md` or `Notes 250420 Sunday.md` with links (e.g., `[Martha](Martha 2025.md)`).

- **PDF Rendering Fails**:
  - Verify `xelatex`:
    ```bash
    docker run --rm -v ~/dev/notes/notes-process:/app -it notes-process xelatex --version
    ```
  - Ensure `_quarto.yml` uses `pdf: documentclass: scrbook`.
  - Share error output for debugging.

- **Slow Rendering**:
  - If new LaTeX packages are downloaded, add them to `Dockerfile`’s `tlmgr install` list.
  - Rebuild:
    ```bash
    docker build -t notes-process .
    ```

## Maintenance

- **Update _quarto.yml**:
  - Add new `.qmd` files to `chapters` in `_quarto.yml` as needed.
  - Example: Add `output/New_Chapter.qmd` to the `chapters` list.

- **Handle New Markdown Formats**:
  - If Obsidian’s export changes frontmatter or image syntax, update `fix_image_paths` or `parse_frontmatter` in `process-vault.py`.
  - Share a sample `.md` file to adjust.

- **Git Workflow**:
  - Commit changes to `process-vault.py`, `_quarto.yml`, `.vscode/`, `Makefile`:
    ```bash
    git add scripts/process-vault.py _quarto.yml
    git commit -m "Update process-vault.py to copy referenced images, add _quarto.yml"
    git push origin master
    ```
  - `input/`, `output/`, `docs/` are ignored (per `.gitignore`).

## Notes

- **Environment**: macOS M2 (ARM64) with Docker Desktop, VS Code, Git.
- **Dependencies**: Docker (`python:3.13-slim-bookworm`, Quarto 1.5.57, TinyTeX), `requirements.txt` (Python packages).
- **Obsidian**: Markdown files with frontmatter (`created`, `date`, `tags`), images in `input/_resources/`.
- **Quarto**: Book project with `scrbook` for PDF, `cosmo` for HTML, EPUB output.
- **Images**: Copied to `output/_resources/` by `process-vault.py`, referenced as `![](_resources/image.jpg)`, copied to `docs/_resources/` by Quarto.
- **PDF**: Uses `xelatex` with pre-installed packages for speed.
- **VS Code**: Use **Run and Debug**, Tasks, or Source Control view.
- **Future Enhancements**:
  - Dynamic `_quarto.yml` chapter generation.
  - Subfolder-based sections (e.g., `Notes 2025Q1` as a chapter).
  - Handle Obsidian `[[links]]`.

For issues or enhancements, open a GitHub issue or share details (e.g., sample `.md` file, error logs) with your collaborator or AI assistant.