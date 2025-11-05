"""Export CWE (Common Weakness Enumeration) reports."""

import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

import yaml


def parse_cwe_spec(spec_file: Path) -> dict:
    """
    Parse the CWE XML specification file.

    Returns a dict with:
    - title: Weakness_Catalog Name attribute
    - version: Weakness_Catalog Version attribute
    - description: Constructed from Name
    - weaknesses: List of dicts with 'id' and 'name' keys
    """
    tree = ET.parse(spec_file)
    root = tree.getroot()

    # Handle XML namespaces
    ns = {"cwe": "http://cwe.mitre.org/cwe-7"}

    # Get catalog info
    catalog_name = root.get("Name", "CWE")
    catalog_version = root.get("Version", "")

    # Collect weaknesses
    weaknesses = []
    for weakness in root.findall(".//cwe:Weakness", ns):
        weakness_id = weakness.get("ID")
        weakness_name = weakness.get("Name")

        if weakness_id and weakness_name:
            weaknesses.append(
                {
                    "id": weakness_id,
                    "name": weakness_name,
                }
            )

    return {
        "title": catalog_name,
        "version": catalog_version,
        "description": f"{catalog_name} - Common Weakness Enumeration",
        "weaknesses": weaknesses,
    }


def parse_top25_spec(spec_file: Path) -> dict:
    """
    Parse a CWE Top 25 XML specification file.

    Returns a dict with:
    - year: Extracted from the Name attribute
    - weakness_ids: List of weakness IDs (strings)
    """
    tree = ET.parse(spec_file)
    root = tree.getroot()

    # Handle XML namespaces
    ns = {"cwe": "http://cwe.mitre.org/cwe-7"}

    # Get catalog info and extract year
    catalog_name = root.get("Name", "")

    # Extract year from name like "VIEW LIST: CWE-1430: Weaknesses in the 2024 CWE Top 25..."
    year = None
    if "20" in catalog_name:
        parts = catalog_name.split()
        for part in parts:
            if part.startswith("20") and len(part) == 4 and part.isdigit():
                year = part
                break

    if not year:
        # Fallback: try to extract from any numeric pattern
        import re

        match = re.search(r"20\d{2}", catalog_name)
        if match:
            year = match.group()

    # Collect weakness IDs
    weakness_ids = []
    for weakness in root.findall(".//cwe:Weakness", ns):
        weakness_id = weakness.get("ID")
        if weakness_id:
            weakness_ids.append(weakness_id)

    return {
        "year": year or "Unknown",
        "weakness_ids": weakness_ids,
    }


def collect_cwe_rules(rules_path: Path) -> Dict[str, Set[str]]:
    """
    Collect rules that reference CWE.

    Returns a dict mapping CWE ID (string) to set of rule IDs.
    """
    rules_map = defaultdict(set)

    if not rules_path.exists():
        return rules_map

    # Iterate through all rule directories
    for rule_dir in rules_path.iterdir():
        if not rule_dir.is_dir():
            continue

        metadata_file = rule_dir / "metadata.json"
        if not metadata_file.exists():
            continue

        try:
            import json

            with metadata_file.open() as f:
                metadata = json.load(f)

            # Check if this rule references CWE
            security_standards = metadata.get("securityStandards", {})
            cwe_list = security_standards.get("CWE", [])

            # Map each CWE ID to this rule
            for cwe_id in cwe_list:
                # CWE IDs in rules are like "CWE-79" or just numbers
                # Normalize to just the number
                cwe_num = str(cwe_id).replace("CWE-", "").replace("CWE", "").strip()
                if cwe_num:
                    rules_map[cwe_num].add(rule_dir.name)

        except Exception:
            # Skip rules with malformed metadata
            continue

    return rules_map


def build_cwe_report(
    cwe_spec: dict,
    cwe_rules: Dict[str, Set[str]],
    top25_specs: List[dict],
) -> dict:
    """
    Build the CWE report structure from the specification and rule mappings.
    """
    # Build main CWE version with all weaknesses
    cwe_categories = []
    cwe_id_to_category = {}  # Map for quick lookup

    for weakness in cwe_spec["weaknesses"]:
        weakness_id = weakness["id"]

        category = {
            "name": weakness_id,
            "description": weakness["name"],
        }

        # Add rules if any are mapped to this weakness
        if weakness_id in cwe_rules and cwe_rules[weakness_id]:
            category["rules"] = sorted(cwe_rules[weakness_id])

        cwe_categories.append(category)
        cwe_id_to_category[weakness_id] = category

    # Build the main CWE version
    main_version = {
        "name": f"{cwe_spec['title']} {cwe_spec['version']}",
        "description": cwe_spec["description"],
        "categories": cwe_categories,
    }

    # Build versions list starting with main CWE
    versions = [main_version]

    # Add Top 25 versions if provided
    for top25 in top25_specs:
        year = top25["year"]
        weakness_ids = top25["weakness_ids"]

        # Build categories for this Top 25 by copying from main CWE
        top25_categories = []

        for weakness_id in weakness_ids:
            # Find the corresponding category in the main CWE version and copy it
            if weakness_id in cwe_id_to_category:
                # Create a copy of the category
                top25_categories.append(dict(cwe_id_to_category[weakness_id]))

        top25_version = {
            "name": f"CWE Top 25 {year}",
            "description": f"CWE Top 25 Most Dangerous Software Weaknesses {year}",
            "categories": top25_categories,
        }

        versions.append(top25_version)

    # Build the complete report with top-level structure wrapped in 'report' key
    return {
        "report": {
            "name": f"{cwe_spec['title']} - Common Weakness Enumeration",
            "description": cwe_spec["description"],
            "classification": "SECURITY",
            "taxonomy": {
                "category": "Weakness",
            },
            "versions": versions,
        }
    }


def export_cwe_report(
    spec_file: Path,
    rules_path: Path,
    output_file: Path,
    top25_specs: List[Path] = None,
) -> dict:
    """
    Export CWE report from XML specification and rule mappings.

    Args:
        spec_file: Path to the main CWE XML specification
        rules_path: Path to the rules directory
        output_file: Path to the output YAML file
        top25_specs: Optional list of paths to Top 25 XML specifications

    Returns:
        The generated report dict
    """
    # Parse the main CWE specification
    cwe_spec = parse_cwe_spec(spec_file)

    # Collect rules that reference CWE
    cwe_rules = collect_cwe_rules(rules_path)

    # Parse Top 25 specifications if provided
    top25_list = []
    if top25_specs:
        for top25_file in top25_specs:
            top25_list.append(parse_top25_spec(top25_file))

    # Build the report
    report = build_cwe_report(cwe_spec, cwe_rules, top25_list)

    # Write to YAML file with custom anchors for categories
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Use custom YAML dumper to create anchors for categories
    _write_cwe_yaml_with_anchors(report, output_file, top25_list)

    return report


def _write_cwe_yaml_with_anchors(
    report: dict, output_file: Path, top25_list: List[dict]
):
    """
    Write CWE report to YAML with anchors for main CWE categories and aliases for Top 25.
    Only creates anchors for CWEs that are referenced in Top 25 lists.
    """
    # Collect all weakness IDs that are referenced in Top 25 lists
    referenced_weakness_ids = set()
    for top25 in top25_list:
        referenced_weakness_ids.update(top25["weakness_ids"])

    with output_file.open("w") as f:
        # Write the report structure manually to control anchor placement
        f.write("report:\n")

        # Write top-level fields
        f.write(f"  name: {_yaml_str(report['report']['name'])}\n")
        f.write(f"  description: {_yaml_str(report['report']['description'])}\n")
        f.write(f"  classification: {report['report']['classification']}\n")
        f.write("  taxonomy:\n")
        f.write("    category: Weakness\n")
        f.write("  versions:\n")

        # Write main CWE version with anchors only for referenced weaknesses
        main_version = report["report"]["versions"][0]
        f.write(f"  - name: {_yaml_str(main_version['name'])}\n")
        f.write(f"    description: {_yaml_str(main_version['description'])}\n")
        f.write("    categories:\n")

        # Write each category, with anchor only if it's referenced in a Top 25
        for category in main_version["categories"]:
            cwe_id = category["name"]

            # Add anchor only if this CWE is referenced in a Top 25 list
            if str(cwe_id) in referenced_weakness_ids:
                f.write(f"    - &cwe{cwe_id}\n")
                f.write(f"      name: {_yaml_str(category['name'])}\n")
            else:
                f.write(f"    - name: {_yaml_str(category['name'])}\n")

            f.write(f"      description: {_yaml_str(category['description'])}\n")

            if "rules" in category:
                f.write("      rules:\n")
                for rule in category["rules"]:
                    f.write(f"      - {rule}\n")

        # Write Top 25 versions with aliases
        for i, top25 in enumerate(top25_list, start=1):
            version = report["report"]["versions"][i]
            f.write(f"  - name: {_yaml_str(version['name'])}\n")
            f.write(f"    description: {_yaml_str(version['description'])}\n")
            f.write("    categories:\n")

            for weakness_id in top25["weakness_ids"]:
                # Write alias to the main CWE category
                f.write(f"    - *cwe{weakness_id}\n")


def _yaml_str(value: str) -> str:
    """Format a string for YAML output."""
    # Always quote strings that might cause issues
    # Check for characters that need quoting
    needs_quoting = (
        "\n" in value
        or ":" in value
        or "#" in value
        or value.startswith(("-", "?", "{", "[", "!", "&", "*", "@", "`", '"', "'"))
        or value.strip() != value
        or len(value) > 80
    )

    if needs_quoting:
        # Use yaml.safe_dump for proper escaping, with large width to prevent wrapping
        dumped = yaml.safe_dump(
            value, default_flow_style=True, allow_unicode=True, width=float("inf")
        ).strip()
        # Remove '...' document end marker if present
        if dumped.endswith("..."):
            dumped = dumped[:-3].strip()
        return dumped

    # Simple string, no quoting needed
    return value
