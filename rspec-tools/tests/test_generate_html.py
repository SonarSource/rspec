import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase

import pytest
from click.testing import CliRunner

from rspec_tools.cli import generate_html


class TestGenerateHtml(TestCase):
    def setUp(self):
        # Create temporary directories for test
        self.test_dir = tempfile.mkdtemp()
        self.rules_dir = Path(self.test_dir) / "rules"
        self.output_dir = Path(self.test_dir) / "output"

        # Create sample rule structure
        self.rule_dir = self.rules_dir / "S123" / "python"
        self.rule_dir.mkdir(parents=True)

        # Create sample rule.adoc file
        self.rule_adoc = self.rule_dir / "rule.adoc"
        with open(self.rule_adoc, "w") as f:
            f.write(
                """= Sample Rule Title
            
== Description

This is a sample rule with a [link](https://example.com).
"""
            )

        # Create sample metadata.json
        self.metadata_json = self.rule_dir / "metadata.json"
        metadata = {
            "title": "Sample Rule",
            "type": "CODE_SMELL",
            "status": "ready",
            "remediation": {"func": "Constant/Issue", "constantCost": "5min"},
            "tags": ["example"],
            "defaultSeverity": "Major",
        }

        with open(self.metadata_json, "w") as f:
            json.dump(metadata, f)

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)

    def test_generate_html(self):
        """Test that generate_html produces the expected output files."""
        runner = CliRunner()
        result = runner.invoke(
            generate_html,
            ["--rules-dir", str(self.rules_dir), "--output-dir", str(self.output_dir)],
        )

        # Check command execution was successful
        assert result.exit_code == 0
        assert f"HTML documentation generated in {self.output_dir}" in result.output

        # Check output HTML file was created
        expected_html = self.output_dir / "S123" / "python" / "rule.html"
        assert expected_html.exists(), f"Expected HTML file not found: {expected_html}"

        # Check content of HTML file
        with open(expected_html, "r") as f:
            html_content = f.read()
            assert "Sample Rule Title" in html_content
            assert "This is a sample rule" in html_content
            assert 'href="https://example.com"' in html_content, "Expected link not found in HTML output"

        # Check metadata.json was copied to output
        expected_metadata = self.output_dir / "S123" / "python" / "metadata.json"
        assert (
            expected_metadata.exists()
        ), f"Expected metadata file not found: {expected_metadata}"

        # Check metadata.json contents match original
        with open(expected_metadata, "r") as f:
            copied_metadata = json.load(f)

        with open(self.metadata_json, "r") as f:
            original_metadata = json.load(f)

        assert copied_metadata == original_metadata, "Metadata files don't match"
