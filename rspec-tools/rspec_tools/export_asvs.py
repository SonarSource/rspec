import json
import yaml
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

from rspec_tools.rules import RulesRepository


def parse_asvs_spec(spec_file: Path) -> dict:
    """Parse the ASVS JSON specification file."""
    with spec_file.open("r") as f:
        return json.load(f)


def collect_asvs_rules(rules_path: Path, standard_name: str) -> Dict[str, Set[str]]:
    """
    Collect all rules that reference the specified security standard.

    Args:
        rules_path: Path to the rules directory
        standard_name: Name of the security standard (e.g., "ASVS 4.0")

    Returns:
        Dictionary mapping requirement IDs to rule sets.
    """
    rule_repository = RulesRepository(rules_path=rules_path)

    # Structure: {requirement_id: set(rule_ids)}
    rules_map = defaultdict(set)

    for rule in rule_repository.rules:
        try:
            # Get security standards from the generic metadata
            security_standards = rule.generic_metadata.get("securityStandards", {})

            if standard_name in security_standards:
                categories = security_standards[standard_name]
                if isinstance(categories, list):
                    for category in categories:
                        rules_map[category].add(rule.id)
        except Exception as e:
            # Skip rules that have errors
            print(f"Warning: Skipping rule {rule.id} due to error: {e}")
            continue

    return rules_map


def build_asvs_report(asvs_spec: dict, asvs_rules: Dict[str, Set[str]]) -> dict:
    """
    Build the ASVS report structure from the specification and rule mappings.
    """
    # Build levels information
    levels = {
        "name": "Application Security Verification Levels",
        "description": "ASVS defines three levels of security verification",
        "inclusive": True,
        "values": [
            {
                "name": "L1",
                "description": "ASVS Level 1 is for low assurance levels, and is completely penetration testable",
            },
            {
                "name": "L2",
                "description": "ASVS Level 2 is for applications that contain sensitive data, which requires protection and is the recommended level for most apps",
            },
            {
                "name": "L3",
                "description": "ASVS Level 3 is for the most critical applications - applications that perform high value transactions, contain sensitive medical data, or any application that requires the highest level of trust",
            },
        ],
    }

    # Build categories from the ASVS specification
    categories = []

    for requirement in asvs_spec.get("Requirements", []):
        # Category name is the shortcode without V prefix
        category_shortcode = requirement["Shortcode"]
        category_name = (
            category_shortcode[1:]
            if category_shortcode.startswith("V")
            else category_shortcode
        )

        category = {
            "name": category_name,
            "description": requirement.get("Name", ""),
            "subcategories": [],
        }

        for item in requirement.get("Items", []):
            # Subcategory name is the shortcode without V prefix
            subcat_shortcode = item["Shortcode"]
            subcat_name = (
                subcat_shortcode[1:]
                if subcat_shortcode.startswith("V")
                else subcat_shortcode
            )

            subcategory = {
                "name": subcat_name,
                "description": item.get("Name", ""),
                "subsubcategories": [],
            }

            for subitem in item.get("Items", []):
                # Subsubcategory name is the shortcode without V prefix
                subsubcat_shortcode = subitem["Shortcode"]
                subsubcat_name = (
                    subsubcat_shortcode[1:]
                    if subsubcat_shortcode.startswith("V")
                    else subsubcat_shortcode
                )

                # Determine the level for this requirement
                level = None
                if subitem.get("L3", {}).get("Required"):
                    level = "Level 3"
                elif subitem.get("L2", {}).get("Required"):
                    level = "Level 2"
                elif subitem.get("L1", {}).get("Required"):
                    level = "Level 1"

                subsubcategory = {
                    "name": subsubcat_name,
                    "description": subitem.get("Description", ""),
                }

                if level:
                    subsubcategory["level"] = level

                # Add rules if any are mapped to this requirement
                # Use the name (shortcode without V) for mapping
                if subsubcat_name in asvs_rules and asvs_rules[subsubcat_name]:
                    subsubcategory["rules"] = sorted(list(asvs_rules[subsubcat_name]))

                subcategory["subsubcategories"].append(subsubcategory)

            if subcategory["subsubcategories"]:
                category["subcategories"].append(subcategory)

        if category["subcategories"]:
            categories.append(category)

    # Build the version object
    version = {
        "name": f"{asvs_spec['ShortName']} {asvs_spec['Version']}",
        "description": asvs_spec.get("Description", ""),
        "categories": categories,
    }

    # Build the complete report
    report = {
        "taxonomy": {
            "category": "Requirement",
            "subcategory": "Requirement",
            "subsubcategory": "Requirement",
        },
        "levels": levels,
        "versions": [version],
    }

    return report


def export_asvs_report(
    spec_file: Path, rules_path: Path, output_file: Path, standard_name: str
) -> dict:
    """
    Export ASVS report from specification and rules.

    Args:
        spec_file: Path to the ASVS JSON specification file
        rules_path: Path to the rules directory
        output_file: Path to the output YAML file
        standard_name: Name of the security standard to filter (e.g., "ASVS 4.0")

    Returns:
        The generated report
    """
    # Parse the ASVS specification
    asvs_spec = parse_asvs_spec(spec_file)

    # Collect rules mapped to ASVS requirements
    asvs_rules = collect_asvs_rules(rules_path, standard_name)

    # Build the report
    report = build_asvs_report(asvs_spec, asvs_rules)

    # Write to YAML file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w") as f:
        yaml.dump(
            report, f, default_flow_style=False, sort_keys=False, allow_unicode=True
        )

    return report
