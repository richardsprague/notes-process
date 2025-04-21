# Notes Process

This project processes markdown files exported from an Obsidian vault (e.g., `~/vaults/notes`, `~/vaults/archive`) into a Quarto book, generating HTML, PDF, and EPUB outputs. It uses Python for preprocessing, Docker for a consistent environment, and TinyTeX for PDF rendering. The workflow is designed for macOS (tested on M2) with VS Code and Git.

## Purpose

- **Input**: Markdown files exported from Obsidian, organized in subfolders (e.g., `input/Notes 2025Q1/`, `input/_resources/` for images).
- **Processing**: Converts `.md` files to `.qmd`, fixes image paths, sorts by date (`created` or `date` frontmatter), and creates a Quarto project.
- **Output**: A book with HTML (`book.html`), PDF (`book.pdf`), and EPUB (`book.epub`) formats, stored in `output/`.

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
├── Dockerfile          # Defines the Docker image with Python, Quarto, TinyTeX
├── requirements.txt    # Python dependencies (pyyaml, markdown, python-dateutil)
├── scripts/
│   └── process_vault.py  # Script to process markdown and generate Quarto project
├── input/              # Exported Obsidian markdown files (ignored by Git)
│   ├── _resources/     # Images referenced in markdown
│   ├── Notes 2025Q1/   # Example subfolder with .md files
│   └── ...
├── output/             # Quarto project and rendered outputs (ignored by Git)
│   ├── _quarto.yml     # Quarto configuration
│   ├── index.qmd       # Book index
│   ├── _resources/     # Copied images
│   ├── chapters/       # Processed .qmd files
│   ├── book.html       # HTML output
│   ├── book.pdf        # PDF output
│   ├── book.epub       # EPUB output
├── .vscode/
│   ├── tasks.json      # VS Code tasks for processing and rendering
│   ├── launch.json     # VS Code debug configurations for Run and Debug menu
├── run.sh              # Shell script for terminal shortcuts
├── .gitignore          # Ignores input/, output/, .vscode/, *.code-workspace
└── README.md           # This file
```

## Setup

1. **Clone the Repository**:
   ```bash
   git clone <your-repo-url>
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
     # File: input/Notes 2025Q1/Notes 2025-01-07.md
     ---
     created: 2025-01-07 06:04
     tags:
       - notes
     ---
     # 2025-01-07 Tuesday
     - Planning meeting
     - ![Image](_resources/aac4c659f4914cfea3aca715d85e69c9.jpg)
     ```

4. **Build the Docker Image**:
   ```bash
   docker build -t notes-process .
   ```
   - This installs Python, Quarto (1.5.57), TinyTeX, and LaTeX packages (`koma-script`, `tcolorbox`, etc.) for rendering.

## Usage

### Option 1: Run via VS Code Run and Debug Menu
1. **Open Project**:
   - Open `~/dev/notes/notes-process` in VS Code.

2. **Run Configurations**:
   - Open the **Run and Debug** panel (`Cmd + Shift + D` or click the play/debug icon in the sidebar).
   - Select a configuration from the dropdown:
     - `Process Notes`: Runs `python scripts/process_vault.py` to process markdown files.
     - `Render Quarto`: Runs `quarto render /app/output` to generate HTML, PDF, and EPUB.
     - `Build Docker Image`: Runs `docker build -t notes-process .` to rebuild the image.
   - Click the green play button or press `F5` to run the selected configuration.
   - Output appears in the integrated terminal.

3. **Optional Shortcuts**:
   - Bind shortcuts in `Code > Preferences > Keyboard Shortcuts` (`Cmd + K, Cmd + S`).
   - Edit `keybindings.json`:
     ```json
     [
       {
         "key": "cmd+shift+p",
         "command": "workbench.action.debug.run",
         "when": "debugConfigurationType == 'node' && debugConfigurationName == 'Process Notes'"
       },
       {
         "key": "cmd+shift+r",
         "command": "workbench.action.debug.run",
         "when": "debugConfigurationType == 'node' && debugConfigurationName == 'Render Quarto'"
       }
     ]
     ```
   - `Cmd + Shift + P` runs `Process Notes`, `Cmd + Shift + R` runs `Render Quarto`.

### Option 2: Run via VS Code Tasks
1. **Open Project**:
   - Open `~/dev/notes/notes-process` in VS Code.

2. **Run Tasks**:
   - Open the Command Palette (`Cmd + Shift + P`).
   - Select `Tasks: Run Task` and choose:
     - `Process Notes`: Processes markdown files.
     - `Render Quarto`: Renders outputs.
     - `Build Docker Image`: Rebuilds the image.
   - Or press `Cmd + Shift + B` to run the default task (`Process Notes`).

### Option 3: Run via Terminal
1. **Using `run.sh`**:
   - Run the shell script for quick terminal access:
     ```bash
     ./run.sh process  # Process markdown files
     ./run.sh render   # Render Quarto project
     ./run.sh build    # Build Docker image
     ```

2. **Using Direct Commands**:
   - Process markdown:
     ```bash
     docker run --rm -v ~/dev/notes/notes-process:/app -it notes-process python scripts/process_vault.py
     ```
   - Render outputs:
     ```bash
     docker run --rm -v ~/dev/notes/notes-process:/app -it notes-process quarto render /app/output
     ```

### View Outputs
- Open in a browser (`book.html`), PDF viewer (`book.pdf`), or e-reader (`book.epub`).
- Check `output/chapters/*.qmd` for processed content.

## Troubleshooting

- **Image Warnings**:
  - If `PandocResourceNotFound` warnings appear (e.g., `chapters/../../_resources/`), ensure `input/_resources/` contains the images and check `.qmd` files for correct paths (`../_resources/`).
  - Share a sample `.md` file with image links to debug.

- **PDF Rendering Fails**:
  - Verify `xelatex`:
    ```bash
    docker run --rm -v ~/dev/notes/notes-process:/app -it notes-process xelatex --version
    ```
  - If it fails, check `_quarto.yml`’s `pdf-engine` (should be `xelatex`) or try `pdflatex`.
  - Share error output for debugging.

- **Slow Rendering**:
  - If new LaTeX packages are downloaded at runtime, add them to the `tlmgr install` list in the Dockerfile (e.g., `tlmgr install <package>`).
  - Rebuild the image:
    ```bash
    docker build -t notes-process .
    ```

- **LuaLaTeX**:
  - If you need `lualatex` (currently deferred), test:
    ```bash
    docker run --rm -v ~/dev/notes/notes-process:/app -it notes-process lualatex --version
    ```
  - If it fails, the Dockerfile includes `lualatex` support, so share the error.

## Maintenance

- **Update LaTeX Packages**:
  - If your markdown requires new LaTeX packages (e.g., for new formatting), add them to the `tlmgr install` line in the Dockerfile and rebuild.
  - Example: `tlmgr install newpackage`.

- **Handle New Markdown Formats**:
  - If Obsidian’s `markdown export` plugin changes frontmatter or image syntax, update `process_vault.py`’s `parse_frontmatter` or `fix_image_paths` functions.
  - Share a sample `.md` file to adjust the script.

- **Git Workflow**:
  - Commit changes to `Dockerfile`, `process_vault.py`, `.vscode/`, or `run.sh`:
    ```bash
    git add <file>
    git commit -m "Update <description>"
    git push origin main
    ```
  - `input/` and `output/` are ignored (per `.gitignore`).

## Notes

- **Environment**: Built for macOS M2 (ARM64) with Docker Desktop, VS Code, and Git.
- **Dependencies**: Managed via Docker (`python:3.13-slim-bookworm`, Quarto 1.5.57, TinyTeX) and `requirements.txt` (Python packages).
- **Obsidian**: Assumes markdown files have frontmatter (`created`, `date`, `tags`) and images in `_resources/`.
- **Quarto**: Configured for a book project with `scrbook` document class for PDF, `cosmo` theme for HTML, and EPUB output.
- **Images**: Handled by copying `_resources/` and rewriting paths to `../_resources/`.
- **PDF**: Uses `xelatex` for rendering, with pre-installed packages for speed.
- **VS Code**: Use the **Run and Debug** panel, Tasks menu, or Source Control view for a streamlined workflow.
- **Future Enhancements**:
  - Chain tasks (e.g., `Process Notes` then `Render Quarto` in one configuration).
  - Support subfolder-based sections in `_quarto.yml` (e.g., `Notes 2025Q1` as a chapter).
  - Handle Obsidian-specific links (e.g., `[[links]]`).

For issues or enhancements, open a GitHub issue or share details (e.g., sample `.md` file, error logs) with your collaborator or AI assistant.