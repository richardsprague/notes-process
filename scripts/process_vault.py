import os
import yaml
import glob
import shutil
import re
from datetime import datetime
from pathlib import Path
from dateutil.parser import parse as parse_date
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Paths (relative to /app in Docker)
INPUT_DIR = Path("/app/input")
OUTPUT_DIR = Path("/app/output")
CHAPTERS_DIR = OUTPUT_DIR / "chapters"
RESOURCES_DIR = INPUT_DIR / "_resources"
OUTPUT_RESOURCES_DIR = OUTPUT_DIR / "_resources"

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
            # Ensure all tags are strings
            frontmatter["tags"] = [str(tag) for tag in tags]
        else:
            logger.warning(f"Invalid tags format in {frontmatter.get('date', frontmatter.get('created', 'unknown'))}: {tags}, removing")
            del frontmatter["tags"]
    return frontmatter

def fix_image_paths(content):
    """Rewrite image paths to use ../_resources/."""
    # Replace ../../_resources/ or similar with ../_resources/
    fixed_content = re.sub(r'(!\[.*?\]\()\s*\.\./\.\./_resources/([^)]+)\)', r'\1../_resources/\2)', content)
    return fixed_content

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

    # Fallback to filename (e.g., Notes 2025-01-04, Notes 250104)
    filename = Path(filename).stem
    for pattern in ["%Y-%m-%d", "%y%m%d"]:
        for part in filename.split():
            try:
                return datetime.strptime(part, pattern)
            except ValueError:
                continue
    
    logger.warning(f"No valid date found for {filename}, using minimum date")
    return datetime.min  # Sort undated files first

def create_quarto_project(files):
    """Create Quarto project structure in output/."""
    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    CHAPTERS_DIR.mkdir(exist_ok=True)

    # Copy _resources directory if it exists
    if RESOURCES_DIR.exists():
        if OUTPUT_RESOURCES_DIR.exists():
            shutil.rmtree(OUTPUT_RESOURCES_DIR)  # Clean previous resources
        shutil.copytree(RESOURCES_DIR, OUTPUT_RESOURCES_DIR)
        logger.info(f"Copied {RESOURCES_DIR} to {OUTPUT_RESOURCES_DIR}")

    # Process markdown files
    chapters = []
    for file in files:
        frontmatter, body = parse_frontmatter(file)
        if not body:  # Skip if parsing failed
            continue
        frontmatter = normalize_tags(frontmatter)  # Fix tags
        body = fix_image_paths(body)  # Fix image paths
        date = get_date(frontmatter, file)
        # Use filename only, flatten subfolders
        output_filename = Path(file).relative_to(INPUT_DIR).with_suffix(".qmd")
        output_filename = output_filename.name  # Avoid subfolder nesting
        output_file = CHAPTERS_DIR / output_filename
        with open(output_file, "w", encoding="utf-8") as f:
            # Write frontmatter
            if frontmatter:
                f.write("---\n")
                yaml.dump(frontmatter, f, allow_unicode=True)
                f.write("---\n\n")
            # Write body
            f.write(body)
        chapters.append((date, output_filename))
        logger.info(f"Processed {file} -> {output_file}")

    # Sort chapters by date
    chapters.sort()  # Sort by date
    chapter_files = [name for _, name in chapters]

    # Create _quarto.yml
    quarto_config = {
        "project": {"type": "book", "output-dir": "."},
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
    with open(OUTPUT_DIR / "index.qmd", "w", encoding="utf-8") as f:
        f.write("# Welcome to Notes 2025\n\nThis is a collection of processed notes.\n")

def main():
    """Process markdown files and create Quarto project."""
    # Get all .md files in input/ and subfolders
    files = glob.glob(str(INPUT_DIR / "**/*.md"), recursive=True)
    if not files:
        logger.error("No markdown files found in input/ or its subfolders")
        return
    create_quarto_project(files)
    logger.info(f"Quarto project created in {OUTPUT_DIR} with {len(files)} files")

if __name__ == "__main__":
    main()