import tempfile
from pathlib import Path

import pytest

from rspec_tools.export_security_standards import (
    build_report_for_standard,
    collect_security_standards,
    export_security_standards,
)


def test_collect_security_standards():
    """Test collecting security standards from test rules."""
    rules_path = Path(__file__).parent.joinpath("resources", "rules")
    standards_map = collect_security_standards(rules_path)

    # Check that we found some standards
    assert len(standards_map) > 0

    # Check that S100 has the expected standards
    assert "ASVS 4.0" in standards_map
    assert "OWASP" in standards_map
    assert "OWASP Top 10 2021" in standards_map

    # Check that the rule is in the right categories
    assert "S100" in standards_map["ASVS 4.0"]["1.23.4"]
    assert "S100" in standards_map["OWASP"]["A1"]
    assert "S100" in standards_map["OWASP Top 10 2021"]["A1"]


def test_build_report_for_standard_flat():
    """Test building report for a standard with flat categories (no dots)."""
    category_rules = {"A1": {"S100", "S200"}, "A2": {"S300"}}

    report = build_report_for_standard("Test Version", category_rules)

    # Check taxonomy
    assert report["taxonomy"]["category"] == "CHANGE ME"
    assert report["taxonomy"]["subcategory"] == "CHANGE ME"
    assert report["taxonomy"]["subsubcategory"] == "CHANGE ME"

    # Check version
    assert len(report["versions"]) == 1
    assert report["versions"][0]["name"] == "Test Version"

    # Check categories (flat structure)
    categories = report["versions"][0]["categories"]
    assert len(categories) == 2

    # Categories should be sorted alphabetically
    assert categories[0]["name"] == "A1"
    assert categories[1]["name"] == "A2"

    # Check rules directly in categories
    assert set(categories[0]["rules"]) == {"S100", "S200"}
    assert set(categories[1]["rules"]) == {"S300"}

    # Should not have subcategories in flat structure
    assert "subcategories" not in categories[0]


def test_build_report_for_standard_hierarchical():
    """Test building report for a standard with hierarchical categories (dots)."""
    category_rules = {
        "1.2.3": {"S100"},
        "1.2.4": {"S200"},
        "1.3.1": {"S300"},
        "2.1.1": {"S400"},
    }

    report = build_report_for_standard("Test Version", category_rules)

    # Check taxonomy
    assert report["taxonomy"]["category"] == "CHANGE ME"

    # Check version
    assert len(report["versions"]) == 1
    version = report["versions"][0]

    # Check hierarchical structure
    categories = version["categories"]
    assert len(categories) == 2  # Categories 1 and 2

    # Check category 1
    cat1 = next(c for c in categories if c["name"] == "1")
    assert "subcategories" in cat1
    assert len(cat1["subcategories"]) == 2  # Subcategories 2 and 3

    # Check subcategory 1.2
    subcat12 = next(s for s in cat1["subcategories"] if s["name"] == "2")
    assert "subsubcategories" in subcat12
    assert len(subcat12["subsubcategories"]) == 2  # Subsubcategories 3 and 4

    # Check subsubcategory 1.2.3
    subsubcat123 = next(
        s for s in subcat12["subsubcategories"] if s["name"] == "3"
    )
    assert set(subsubcat123["rules"]) == {"S100"}


def test_export_security_standards():
    """Test exporting a specific security standard to a YAML file."""
    rules_path = Path(__file__).parent.joinpath("resources", "rules")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Export OWASP standard
        report = export_security_standards("OWASP", rules_path, output_dir)

        # Check that the file was created
        output_file = output_dir / "OWASP.yaml"
        assert output_file.exists()

        # Check that the report has the expected structure
        assert "taxonomy" in report
        assert "versions" in report
        assert len(report["versions"]) == 1
        # Version name should be the standard name
        assert report["versions"][0]["name"] == "OWASP"

        # Check that the YAML file is valid
        import yaml

        with output_file.open("r") as f:
            loaded_report = yaml.safe_load(f)

        assert loaded_report == report


def test_export_security_standards_not_found():
    """Test that exporting a non-existent security standard raises an error."""
    rules_path = Path(__file__).parent.joinpath("resources", "rules")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Try to export a non-existent standard
        with pytest.raises(ValueError, match="Security standard.*not found"):
            export_security_standards("NonExistent", rules_path, output_dir)

