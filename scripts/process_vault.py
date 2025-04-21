import os
import yaml
import glob
import shutil
import re
from datetime import datetime
from pathlib import Path
from dateutil.parser import parse as parse_date
import logging
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Paths (relative to /app in Docker)
INPUT_DIR = Path("/app/input")
OUTPUT_DIR = Path("/app/output")
CHAPTERS_DIR = OUTPUT_DIR / "chapters"
RESOURCES_DIR = INPUT_DIR / "_resources"
OUTPUT_RESOURCES_DIR = OUTPUT_DIR / "docs" / "_resources"

def parse_frontmatter(file_path):
    """Parse frontmatter and content from a markdown file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                    return frontmatter or {}, body
            return {}, content
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
        return {}, ""

def normalize_tags(frontmatter):
    """Ensure tags is an array of strings."""
    if "tags" in frontmatter:
        tags = frontmatter["tags"]
        if isinstance(tags, str):
            frontmatter["tags"] = [tags]
            logger.info(f"Converted tags to array in {frontmatter.get('date', frontmatter.get('created', 'unknown'))}: {frontmatter['tags']}")
        elif isinstance(tags, list):
            frontmatter["tags"] = [str(tag) for tag in tags]
        else:
            logger.warning(f"Invalid tags format in {frontmatter.get('date', frontmatter.get('created', 'unknown'))}: {tags}, removing")
            del frontmatter["tags"]
    return frontmatter

def fix_image_paths(content, is_index=False):
    """Rewrite image paths to _resources/ for index.qmd or ../_resources/ for chapters."""
    def replace_image(match):
        link_text = match.group(1)
        image_path = match.group(2)
        dir_path = "_resources" if is_index else "../_resources"
        new_path = f"{dir_path}/{Path(image_path).name}"
        logger.info(f"Rewriting image path: {image_path} -> {new_path}")
        return f"{link_text}{new_path})"

    # Match image links like ![text](_resources/image.jpg) or ![text](chapters/../../_resources/image.jpg)
    pattern = r'(!\[.*?\]\()\s*(?:(?:chapters/)?\.\./)*_resources/([^)]+)\)?'
    return re.sub(pattern, replace_image, content)

def fix_internal_links(content, file_map):
    """Convert Obsidian-style internal links to HTML links."""
    def replace_link(match):
        link_text = match.group(1)
        link_url = match.group(2)
        # Decode URL-encoded spaces (%20)
        link_url_decoded = link_url.replace("%20", " ")
        # Check if the linked file exists in file_map
        for input_file, html_name in file_map.items():
            if Path(input_file).name == link_url_decoded:
                logger.info(f"Resolved link: {link_url} -> {html_name}")
                return f"[{link_text}]({html_name})"
        # Log unresolved link and preserve as-is
        logger.warning(f"Unresolved link target in {content[:50]}...: {link_url}")
        return match.group(0)

    # Match Markdown links like [text](filename.md)
    return re.sub(r'\[([^\]]*)\]\(([^)]+\.md)\)', replace_link, content)

def get_date(frontmatter, filename):
    """Extract date from frontmatter (date or created) or filename."""
    for date_field in ["date", "created"]:
        if frontmatter.get(date_field):
            try:
                date_str = str(frontmatter[date_field])
                parsed_date = parse_date(date_str, fuzzy=True).replace(tzinfo=None)
                return parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)  # Strip time
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid {date_field} in frontmatter of {filename}: {e}")

    # Fallback to filename (e.g., Notes YYMMDD)
    filename = Path(filename).stem
    match = re.match(r"Notes (\d{6})", filename)
    if match:
        try:
            return datetime.strptime(match.group(1), "%y%m%d")
        except ValueError:
            pass
    
    logger.warning(f"No valid date found for {filename}, using minimum date")
    return datetime.min  # Sort undated files first

def format_notes_date(filename):
    """Format date for Notes files as date-box div."""
    match = re.match(r"Notes (\d{6})(?: \w+)?", Path(filename).stem)
    if match:
        d = datetime.strptime(match.group(1), '%y%m%d').date()
        date_str = d.strftime("%A, %B %d")
        return f'<div class="raw"><p class="date-box">{date_str}</p></div>'
    return f'<div class="raw"><p class="date-box">{Path(filename).stem}</p></div>'

def create_quarto_project(files):
    """Create Quarto project structure in output/."""
    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    CHAPTERS_DIR.mkdir(exist_ok=True)
    OUTPUT_RESOURCES_DIR.parent.mkdir(exist_ok=True)  # Ensure docs/ exists

    # Separate Notes files (Notes YYMMDD* with tag: notes) and others
    notes_files = []
    other_files = []
    for f in files:
        frontmatter, _ = parse_frontmatter(f)
        if (re.match(r"Notes \d{6}.*", Path(f).name) and
            frontmatter.get("tags") and ("notes" in frontmatter["tags"] or frontmatter["tags"] == "notes")):
            notes_files.append(f)
        else:
            other_files.append(f)

    # Track file mappings for links
    file_map = {}  # {input_path: html_name}
    for f in files:
        fname = Path(f).relative_to(INPUT_DIR).with_suffix(".html").name
        file_map[f] = fname

    # Process non-Notes files as individual chapters
    chapters = []
    for file in other_files:
        frontmatter, body = parse_frontmatter(file)
        if not body:
            continue
        frontmatter = normalize_tags(frontmatter)
        body = fix_image_paths(body, is_index=False)
        body = fix_internal_links(body, file_map)
        date = get_date(frontmatter, file)
        output_filename = Path(file).relative_to(INPUT_DIR).with_suffix(".qmd").name
        output_file = CHAPTERS_DIR / output_filename
        with open(output_file, "w", encoding="utf-8") as f:
            if frontmatter:
                f.write("---\n")
                yaml.dump(frontmatter, f, allow_unicode=True)
                f.write("---\n\n")
            f.write(body)
        chapters.append((date, output_filename))
        logger.info(f"Processed {file} -> {output_file}")

    # Concatenate Notes files into Notes-All.qmd
    if notes_files:
        notes_files.sort(key=lambda x: get_date(parse_frontmatter(x)[0], x))  # Sort by date
        notes_content = []
        for file in notes_files:
            frontmatter, body = parse_frontmatter(file)
            if not body:
                continue
            body = fix_image_paths(body, is_index=False)  # Apply image path fix for chapters
            date_box = format_notes_date(file)
            notes_content.append(f"{date_box}\n{body}")
        notes_all_file = CHAPTERS_DIR / "Notes-All.qmd"
        with open(notes_all_file, "w", encoding="utf-8") as f:
            f.write("# All Notes\n\n")
            f.write(fix_internal_links("\n".join(notes_content), file_map))
        chapters.append((datetime.min, "Notes-All.qmd"))  # Add at start
        logger.info(f"Created {notes_all_file} with {len(notes_files)} notes")

    # Sort chapters by date
    chapters.sort()
    chapter_files = [name for _, name in chapters]

    # Create _quarto.yml
    quarto_config = {
        "project": {"type": "book", "output-dir": "docs"},
        "book": {
            "title": "Notes 2025",
            "author": "Sprague",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "chapters": ["index.qmd"] + [f"chapters/{f}" for f in chapter_files],
        },
        "format": {
            "html": {"theme": "cosmo"},
            "pdf": {"documentclass": "scrbook"},
            "epub": {},
        },
    }
    with open(OUTPUT_DIR / "_quarto.yml", "w", encoding="utf-8") as f:
        yaml.dump(quarto_config, f, allow_unicode=True)

    # Create index.qmd
    index_file = OUTPUT_DIR / "index.qmd"
    with open(index_file, "w", encoding="utf-8") as f:
        body = "# Welcome to Notes 2025\n\nThis is a collection of processed notes.\n"
        body = fix_image_paths(body, is_index=True)  # Apply image path fix for index
        f.write(body)

    # Run Quarto render
    logger.info("Running Quarto render...")
    try:
        subprocess.run(["quarto", "render", str(OUTPUT_DIR)], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Quarto render failed: {e}")
        return

    # Copy _resources to output/docs/_resources after render
    if RESOURCES_DIR.exists():
        if OUTPUT_RESOURCES_DIR.exists():
            shutil.rmtree(OUTPUT_RESOURCES_DIR)  # Clean any existing resources
        shutil.copytree(RESOURCES_DIR, OUTPUT_RESOURCES_DIR)
        logger.info(f"Copied {RESOURCES_DIR} to {OUTPUT_RESOURCES_DIR} after render")

def main():
    """Process markdown files and create Quarto project."""
    # Get all .md files strictly under input/ subdirectories
    files = [
        f for f in glob.glob(str(INPUT_DIR / "**/*.md"), recursive=True)
        if Path(f).is_file() and Path(f).parent.resolve() != Path("/app").resolve()
    ]
    if not files:
        logger.error("No markdown files found in input/ or its subfolders")
        return
    create_quarto_project(files)
    logger.info(f"Quarto project created in {OUTPUT_DIR} with {len(files)} files")

if __name__ == "__main__":
    main()