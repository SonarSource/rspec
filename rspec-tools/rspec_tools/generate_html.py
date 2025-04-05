import shutil
from pathlib import Path

import click
import subprocess

def generate_html_docs(output_dir: str, rules_dir: str):
    """Generate HTML documentation from rule AsciiDoc files."""
    out_dir = Path(output_dir)
    out_dir.mkdir(exist_ok=True)

    # Run asciidoctor to generate HTML files
    rules_dir = Path(rules_dir)
    if not rules_dir.exists():
        raise click.ClickException(f"Rules directory not found: {rules_dir}")

    try:
        subprocess.run(
            [
                "asciidoctor",
                "-R",
                str(rules_dir),
                "-D",
                str(out_dir),
                f"{rules_dir}/*/*/rule.adoc",
                "-q",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"Error running asciidoctor: {e}")

    # Copy metadata.json files to output directory
    for metadata_file in rules_dir.glob("**/metadata.json"):
        # Create relative path to preserve directory structure
        rel_path = metadata_file.relative_to(rules_dir)
        dest_path = out_dir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(metadata_file, dest_path)

    return out_dir
