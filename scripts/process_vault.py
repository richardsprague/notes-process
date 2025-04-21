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
RESOURCES_DIR = INPUT_DIR / "_resources"
OUTPUT_RESOURCES_DIR = OUTPUT_DIR / "_resources"

def parse_frontmatter(file_path):
    """Parse frontmatter and content, sanitizing line terminators."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Replace Unicode LS (U+2028) and PS (U+2029) with \n
            content = content.replace('\u2028', '\n').replace('\u2029', '\n')
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

def fix_image_paths(content, image_set, file_path):
    """Rewrite image paths to _resources/, preserving captions and copying images."""
    def replace_image(match):
        caption = match.group(2)  # e.g., caption or empty string
        image_path = match.group(3)  # e.g., image.jpg
        if not image_path or not re.match(r'.+\.(jpg|jpeg|png|gif)$', image_path, re.IGNORECASE):
            logger.warning(f"Skipping malformed image link in {file_path}: {match.group(0)}")
            return match.group(0)
        new_path = f"_resources/{Path(image_path).name}"
        image_set.add(Path(image_path).name)
        logger.info(f"Rewriting image path in {file_path}: {image_path} -> {new_path} with caption: '{caption}'")
        return f"![{caption}]({new_path})"

    # Match image links like ![caption](_resources/image.jpg) or ![caption](.../_resources/image.jpg)
    pattern = r'(!\[([^\]]*)\]\()\s*(?:\.\./)*_resources/([^/\s)]+\.(?:jpg|jpeg|png|gif))\)?'
    return re.sub(pattern, replace_image, content)

def copy_referenced_images(image_set):
    """Copy referenced images to output/_resources/."""
    OUTPUT_RESOURCES_DIR.mkdir(exist_ok=True)
    for image in image_set:
        if not image:
            logger.warning("Skipping empty image name in image_set")
            continue
        src = RESOURCES_DIR / image
        dst = OUTPUT_RESOURCES_DIR / image
        if src.is_file():
            shutil.copy2(src, dst)
            logger.info(f"Copied {src} to {dst}")
        else:
            logger.warning(f"Image not found or is a directory: {src}")

def fix_internal_links(content, file_map):
    """Convert Obsidian-style internal links to qmd links."""
    def replace_link(match):
        link_text = match.group(1)
        link_url = match.group(2)
        link_url_decoded = link_url.replace("%20", " ")
        for input_file, qmd_name in file_map.items():
            if Path(input_file).name == link_url_decoded:
                logger.info(f"Resolved link: {link_url} -> {qmd_name}")
                return f"[{link_text}]({qmd_name})"
        logger.warning(f"Unresolved link target in {content[:50]}...: {link_url}")
        return match.group(0)

    pattern = r'\[([^\]]*)\]\(([^)]+\.md)\)'
    return re.sub(pattern, replace_link, content)

def get_date(frontmatter, filename):
    """Extract date from frontmatter (date or created) or filename."""
    for date_field in ["date", "created"]:
        if frontmatter.get(date_field):
            try:
                date_str = str(frontmatter[date_field])
                parsed_date = parse_date(date_str, fuzzy=True).replace(tzinfo=None)
                return parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid {date_field} in frontmatter of {filename}: {e}")

    filename = Path(filename).stem
    match = re.match(r"Notes (\d{6})", filename)
    if match:
        try:
            return datetime.strptime(match.group(1), "%y%m%d")
        except ValueError:
            pass
    
    logger.warning(f"No valid date found for {filename}, using minimum date")
    return datetime.min

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
    OUTPUT_DIR.mkdir(exist_ok=True)
    image_set = set()  # Track referenced images

    notes_files = []
    other_files = []
    file_map = {}  # {input_path: qmd_name}
    for f in files:
        frontmatter, _ = parse_frontmatter(f)
        qmd_name = Path(f).relative_to(INPUT_DIR).with_suffix(".qmd").name
        file_map[f] = qmd_name
        if (re.match(r"Notes \d{6}.*", Path(f).name) and
            frontmatter.get("tags") and ("notes" in frontmatter["tags"] or frontmatter["tags"] == "notes")):
            notes_files.append(f)
        else:
            other_files.append(f)

    for file in other_files:
        frontmatter, body = parse_frontmatter(file)
        if not body:
            continue
        frontmatter = normalize_tags(frontmatter)
        body = fix_image_paths(body, image_set, file)
        body = fix_internal_links(body, file_map)
        output_filename = Path(file).relative_to(INPUT_DIR).with_suffix(".qmd").name
        output_file = OUTPUT_DIR / output_filename
        with open(output_file, "w", encoding="utf-8") as f:
            if frontmatter:
                f.write("---\n")
                yaml.dump(frontmatter, f, allow_unicode=True)
                f.write("---\n\n")
            f.write(body)
        logger.info(f"Processed {file} -> {output_file}")

    if notes_files:
        notes_files.sort(key=lambda x: get_date(parse_frontmatter(x)[0], x))
        notes_content = []
        for file in notes_files:
            frontmatter, body = parse_frontmatter(file)
            if not body:
                continue
            body = fix_image_paths(body, image_set, file)
            body = fix_internal_links(body, file_map)
            date_box = format_notes_date(file)
            notes_content.append(f"{date_box}\n{body}")
        notes_all_file = OUTPUT_DIR / "Notes-All.qmd"
        with open(notes_all_file, "w", encoding="utf-8") as f:
            f.write("# All Notes\n\n")
            f.write("\n".join(notes_content))
        logger.info(f"Created {notes_all_file} with {len(notes_files)} notes")

    copy_referenced_images(image_set)

    index_file = OUTPUT_DIR / "index.qmd"
    with open(index_file, "w", encoding="utf-8") as f:
        body = "# Welcome to Notes 2025\n\nThis is a collection of processed notes.\n"
        body = fix_image_paths(body, image_set, index_file)
        f.write(body)
        logger.info(f"Created {index_file}")

def main():
    """Process markdown files and create Quarto project."""
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