import xml.etree.ElementTree as ET
import yaml
from pathlib import Path
from typing import Dict, Set
from collections import defaultdict

from rspec_tools.rules import RulesRepository


def parse_stig_spec(spec_file: Path) -> dict:
    """Parse the STIG XML specification file."""
    tree = ET.parse(spec_file)
    root = tree.getroot()
    
    # Define namespace
    ns = {'xccdf': 'http://checklists.nist.gov/xccdf/1.1'}
    
    # Extract Benchmark information
    title_elem = root.find('xccdf:title', ns)
    desc_elem = root.find('xccdf:description', ns)
    
    # Extract all Groups
    groups = []
    for group in root.findall('xccdf:Group', ns):
        group_id = group.get('id')
        
        # Get the Rule title (there should be a single Rule inside each Group)
        rule = group.find('xccdf:Rule', ns)
        rule_title = ''
        if rule is not None:
            rule_title_elem = rule.find('xccdf:title', ns)
            rule_title = rule_title_elem.text if rule_title_elem is not None else ''
        
        groups.append({
            'id': group_id,
            'description': rule_title
        })
    
    return {
        'title': title_elem.text if title_elem is not None else '',
        'description': desc_elem.text if desc_elem is not None else '',
        'groups': groups
    }


def collect_stig_rules(rules_path: Path, standard_name: str) -> Dict[str, Set[str]]:
    """
    Collect all rules that reference the specified STIG standard.
    
    Args:
        rules_path: Path to the rules directory
        standard_name: Name of the security standard (e.g., "STIG ASD_V5R3")
    
    Returns:
        Dictionary mapping Group IDs to rule sets.
    """
    rule_repository = RulesRepository(rules_path=rules_path)
    
    # Structure: {group_id: set(rule_ids)}
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


def build_stig_report(stig_spec: dict, stig_rules: Dict[str, Set[str]], standard_name: str) -> dict:
    """
    Build the STIG report structure from the specification and rule mappings.
    """
    # Build categories from the STIG specification
    categories = []
    
    for group in stig_spec.get("groups", []):
        group_id = group['id']
        
        category = {
            "name": group_id,
            "description": group.get('description', ''),
        }
        
        # Add rules if any are mapped to this group
        if group_id in stig_rules and stig_rules[group_id]:
            category["rules"] = sorted(list(stig_rules[group_id]))
        
        categories.append(category)
    
    # Build the version object
    version = {
        "name": standard_name,
        "description": stig_spec.get("description", ""),
        "categories": categories,
    }
    
    # Build the complete report with top-level structure wrapped in 'report' key
    return {
        "report": {
            "name": stig_spec.get("title", standard_name),
            "description": stig_spec.get("description", ""),
            "classification": "SECURITY",
            "taxonomy": {
                "category": "Group",
            },
            "versions": [version],
        }
    }


def export_stig_report(
    spec_file: Path, rules_path: Path, output_file: Path, standard_name: str
) -> dict:
    """
    Export STIG report from specification and rules.
    
    Args:
        spec_file: Path to the STIG XML specification file
        rules_path: Path to the rules directory
        output_file: Path to the output YAML file
        standard_name: Name of the security standard to filter (e.g., "STIG ASD_V5R3")
    
    Returns:
        The generated report
    """
    # Parse the STIG specification
    stig_spec = parse_stig_spec(spec_file)
    
    # Collect rules mapped to STIG groups
    stig_rules = collect_stig_rules(rules_path, standard_name)
    
    # Build the report
    report = build_stig_report(stig_spec, stig_rules, standard_name)
    
    # Write to YAML file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w") as f:
        yaml.dump(
            report, f, default_flow_style=False, sort_keys=False, allow_unicode=True
        )
    
    return report

