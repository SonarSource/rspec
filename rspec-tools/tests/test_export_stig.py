"""Tests for STIG export functionality."""

import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import json

import pytest
import yaml
from jsonschema import validate, ValidationError

from rspec_tools.export_stig import (
    parse_stig_spec,
    collect_stig_rules,
    build_stig_report,
    export_stig_report,
)


@pytest.fixture
def sample_stig_xml(tmp_path):
    """Create a sample STIG XML specification file."""
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Benchmark xmlns="http://checklists.nist.gov/xccdf/1.1" id="test_stig">
    <title>Test STIG Security Technical Implementation Guide</title>
    <description>This is a test STIG specification</description>
    <Group id="V-222387">
        <title>SRG-APP-000001</title>
        <description>Group description</description>
        <Rule id="SV-222387r879511_rule">
            <title>The application must provide a capability to limit the number of logon sessions per user.</title>
        </Rule>
    </Group>
    <Group id="V-222388">
        <title>SRG-APP-000295</title>
        <description>Group description 2</description>
        <Rule id="SV-222388r879673_rule">
            <title>The application must clear temporary storage and cookies when the session is terminated.</title>
        </Rule>
    </Group>
</Benchmark>'''
    
    xml_file = tmp_path / "test_stig.xml"
    xml_file.write_text(xml_content)
    return xml_file


def test_parse_stig_spec(sample_stig_xml):
    """Test parsing STIG XML specification."""
    spec = parse_stig_spec(sample_stig_xml)
    
    assert spec["title"] == "Test STIG Security Technical Implementation Guide"
    assert spec["description"] == "This is a test STIG specification"
    assert len(spec["groups"]) == 2
    assert spec["groups"][0]["id"] == "V-222387"
    assert spec["groups"][0]["description"] == "The application must provide a capability to limit the number of logon sessions per user."
    assert spec["groups"][1]["id"] == "V-222388"
    assert spec["groups"][1]["description"] == "The application must clear temporary storage and cookies when the session is terminated."


def test_collect_stig_rules(mockrules):
    """Test collecting rules that reference STIG standards."""
    # Use the test rules directory
    stig_rules = collect_stig_rules(mockrules, "STIG ASD_V5R3")
    
    # Should be a dictionary mapping group IDs to rule sets
    assert isinstance(stig_rules, dict)
    
    # Each value should be a set of rule IDs
    for group_id, rule_ids in stig_rules.items():
        assert isinstance(group_id, str)
        assert isinstance(rule_ids, set)
        for rule_id in rule_ids:
            assert rule_id.startswith("S")


def test_build_stig_report():
    """Test building STIG report structure."""
    stig_spec = {
        "title": "Test STIG",
        "description": "Test description",
        "groups": [
            {"id": "V-222387", "description": "Rule description 1"},
            {"id": "V-222388", "description": "Rule description 2"},
        ]
    }
    
    stig_rules = {
        "V-222387": {"S100", "S101"},
        "V-222388": {"S200"},
    }
    
    result = build_stig_report(stig_spec, stig_rules, "STIG ASD_V5R3")
    
    # Check top-level has 'report' key
    assert "report" in result
    report = result["report"]
    
    # Check top-level fields
    assert report["name"] == "Test STIG"
    assert report["description"] == "Test description"
    assert report["classification"] == "SECURITY"
    
    # Check taxonomy
    assert report["taxonomy"]["category"] == "Group"
    
    # Check version
    assert len(report["versions"]) == 1
    version = report["versions"][0]
    assert version["name"] == "STIG ASD_V5R3"
    assert version["description"] == "Test description"
    
    # Check categories
    assert len(version["categories"]) == 2
    
    # First category
    cat1 = version["categories"][0]
    assert cat1["name"] == "V-222387"
    assert cat1["description"] == "Rule description 1"
    assert set(cat1["rules"]) == {"S100", "S101"}
    
    # Second category
    cat2 = version["categories"][1]
    assert cat2["name"] == "V-222388"
    assert cat2["description"] == "Rule description 2"
    assert cat2["rules"] == ["S200"]


def test_export_stig_report(sample_stig_xml, mockrules, tmp_path):
    """Test end-to-end STIG report export."""
    output_file = tmp_path / "stig_report.yaml"
    
    result = export_stig_report(
        sample_stig_xml, mockrules, output_file, "STIG ASD_V5R3"
    )
    
    # Check the top-level structure has 'report' key
    assert "report" in result
    report = result["report"]
    
    # Check the report structure
    assert "name" in report
    assert "description" in report
    assert "classification" in report
    assert report["classification"] == "SECURITY"
    assert "taxonomy" in report
    assert report["taxonomy"]["category"] == "Group"
    assert "versions" in report
    assert len(report["versions"]) == 1
    
    # Check the output file was created
    assert output_file.exists()
    
    # Load and verify the YAML file
    with output_file.open() as f:
        yaml_data = yaml.safe_load(f)
    
    assert "report" in yaml_data
    assert yaml_data["report"]["name"] == "Test STIG Security Technical Implementation Guide"
    assert yaml_data["report"]["classification"] == "SECURITY"
    assert yaml_data["report"]["taxonomy"]["category"] == "Group"
    assert len(yaml_data["report"]["versions"]) == 1
    assert yaml_data["report"]["versions"][0]["name"] == "STIG ASD_V5R3"


def test_stig_report_validates_against_schema(sample_stig_xml, mockrules, tmp_path):
    """Test that the generated STIG report validates against the JSON schema."""
    output_file = tmp_path / "stig_report.yaml"
    
    # Generate the report
    result = export_stig_report(
        sample_stig_xml, mockrules, output_file, "STIG ASD_V5R3"
    )
    
    # Load the JSON schema
    schema_path = Path(__file__).parent.parent / "rspec_tools" / "report.schema.json"
    with schema_path.open() as f:
        schema = json.load(f)
    
    # The report is under the 'report' key, so validate that part
    assert "report" in result
    
    # Validate the report against the schema
    try:
        validate(instance=result["report"], schema=schema)
    except ValidationError as e:
        pytest.fail(f"STIG report does not validate against schema: {e.message}")


