import json
import tempfile
from pathlib import Path

import pytest

from rspec_tools.export_asvs import (
    build_asvs_report,
    collect_asvs_rules,
    export_asvs_report,
    parse_asvs_spec,
)


def test_parse_asvs_spec():
    """Test parsing ASVS specification file."""
    # Create a minimal ASVS spec
    spec_data = {
        "Name": "Application Security Verification Standard Project",
        "ShortName": "ASVS",
        "Version": "4.0.3",
        "Description": "Test description",
        "Requirements": [
            {
                "Shortcode": "V1",
                "Name": "Test Category",
                "Items": [
                    {
                        "Shortcode": "V1.1",
                        "Name": "Test Subcategory",
                        "Items": [
                            {
                                "Shortcode": "V1.1.1",
                                "Description": "Test requirement",
                                "L1": {"Required": False},
                                "L2": {"Required": True},
                                "L3": {"Required": True},
                            }
                        ],
                    }
                ],
            }
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(spec_data, f)
        spec_file = Path(f.name)

    try:
        spec = parse_asvs_spec(spec_file)
        assert spec["ShortName"] == "ASVS"
        assert spec["Version"] == "4.0.3"
        assert len(spec["Requirements"]) == 1
    finally:
        spec_file.unlink()


def test_collect_asvs_rules():
    """Test collecting rules with ASVS 4.0 mappings."""
    rules_path = Path(__file__).parent.joinpath("resources", "rules")
    asvs_rules = collect_asvs_rules(rules_path, "ASVS 4.0")

    # Check that we found ASVS mappings
    assert len(asvs_rules) > 0

    # Check that S100 is mapped to 1.23.4
    assert "1.23.4" in asvs_rules
    assert "S100" in asvs_rules["1.23.4"]


def test_build_asvs_report():
    """Test building ASVS report from spec and rules."""
    spec_data = {
        "Name": "Application Security Verification Standard Project",
        "ShortName": "ASVS",
        "Version": "4.0.3",
        "Description": "Test description",
        "Requirements": [
            {
                "Shortcode": "V1",
                "Name": "Test Category",
                "Items": [
                    {
                        "Shortcode": "V1.1",
                        "Name": "Test Subcategory",
                        "Items": [
                            {
                                "Shortcode": "V1.1.1",
                                "Description": "Test requirement L2",
                                "L1": {"Required": False},
                                "L2": {"Required": True},
                                "L3": {"Required": True},
                            },
                            {
                                "Shortcode": "V1.1.2",
                                "Description": "Test requirement L1",
                                "L1": {"Required": True},
                                "L2": {"Required": True},
                                "L3": {"Required": True},
                            },
                        ],
                    }
                ],
            }
        ],
    }

    asvs_rules = {"1.1.1": {"S100", "S200"}, "1.1.2": {"S300"}}

    report = build_asvs_report(spec_data, asvs_rules)

    # Check taxonomy
    assert report["taxonomy"]["category"] == "Requirement"
    assert report["taxonomy"]["subcategory"] == "Requirement"
    assert report["taxonomy"]["subsubcategory"] == "Requirement"

    # Check levels
    assert "levels" in report
    levels = report["levels"]
    assert levels["name"] == "Application Security Verification Levels"
    assert len(levels["values"]) == 3
    assert levels["values"][0]["name"] == "Level 1"
    assert levels["values"][1]["name"] == "Level 2"
    assert levels["values"][2]["name"] == "Level 3"

    # Check version
    assert len(report["versions"]) == 1
    version = report["versions"][0]
    assert version["name"] == "ASVS 4.0.3"
    assert version["description"] == "Test description"

    # Check categories
    categories = version["categories"]
    assert len(categories) == 1
    assert categories[0]["name"] == "1"  # Shortcode without V
    assert categories[0]["description"] == "Test Category"

    # Check subcategories
    subcategories = categories[0]["subcategories"]
    assert len(subcategories) == 1
    assert subcategories[0]["name"] == "1.1"  # Shortcode without V
    assert subcategories[0]["description"] == "Test Subcategory"

    # Check subsubcategories (requirements)
    subsubcategories = subcategories[0]["subsubcategories"]
    assert len(subsubcategories) == 2

    # Check first requirement (L2)
    req1 = subsubcategories[0]
    assert req1["name"] == "1.1.1"  # Shortcode without V
    assert req1["description"] == "Test requirement L2"
    assert req1["level"] == "Level 3"
    assert set(req1["rules"]) == {"S100", "S200"}

    # Check second requirement (L1)
    req2 = subsubcategories[1]
    assert req2["name"] == "1.1.2"  # Shortcode without V
    assert req2["description"] == "Test requirement L1"
    assert req2["level"] == "Level 3"
    assert set(req2["rules"]) == {"S300"}


def test_export_asvs_report():
    """Test exporting ASVS report to YAML file."""
    # Create a minimal ASVS spec
    spec_data = {
        "Name": "Application Security Verification Standard Project",
        "ShortName": "ASVS",
        "Version": "4.0.3",
        "Description": "Test description",
        "Requirements": [
            {
                "Shortcode": "V1",
                "Name": "Test Category",
                "Items": [
                    {
                        "Shortcode": "V1.1",
                        "Name": "Test Subcategory",
                        "Items": [
                            {
                                "Shortcode": "V1.23.4",
                                "Description": "Test requirement",
                                "L1": {"Required": False},
                                "L2": {"Required": True},
                                "L3": {"Required": True},
                            }
                        ],
                    }
                ],
            }
        ],
    }

    rules_path = Path(__file__).parent.joinpath("resources", "rules")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create spec file
        spec_file = Path(tmpdir) / "asvs-spec.json"
        with spec_file.open("w") as f:
            json.dump(spec_data, f)

        # Export report
        output_file = Path(tmpdir) / "asvs-report.yaml"
        report = export_asvs_report(spec_file, rules_path, output_file, "ASVS 4.0")

        # Check that the file was created
        assert output_file.exists()

        # Check report structure
        assert "taxonomy" in report
        assert "levels" in report
        assert "versions" in report
        assert len(report["versions"]) == 1

        # Check that the YAML file is valid
        import yaml

        with output_file.open("r") as f:
            loaded_report = yaml.safe_load(f)

        assert loaded_report == report

        # Check that S100 is mapped to 1.23.4
        version = loaded_report["versions"][0]
        category = version["categories"][0]
        subcategory = category["subcategories"][0]
        requirement = subcategory["subsubcategories"][0]
        assert "S100" in requirement.get("rules", [])

