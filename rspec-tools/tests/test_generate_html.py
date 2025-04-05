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
            assert (
                'href="https://example.com"' in html_content
            ), "Expected link not found in HTML output"

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

    def test_generate_html_multiple_rules(self):
        """Test that generate_html processes multiple rules with multiple language specializations."""
        # Create a second rule for python
        rule2_dir = self.rules_dir / "S456" / "python"
        rule2_dir.mkdir(parents=True)

        with open(rule2_dir / "rule.adoc", "w") as f:
            f.write(
                "= Second Rule Python\n\n== Description\n\nSecond rule python description."
            )

        with open(rule2_dir / "metadata.json", "w") as f:
            json.dump({"title": "Second Rule Python", "status": "ready"}, f)

        # Add cfamily specialization for first rule
        cfamily1_dir = self.rules_dir / "S123" / "cfamily"
        cfamily1_dir.mkdir(parents=True)

        with open(cfamily1_dir / "rule.adoc", "w") as f:
            f.write(
                "= First Rule CFamily\n\n== Description\n\nFirst rule cfamily description."
            )

        with open(cfamily1_dir / "metadata.json", "w") as f:
            json.dump({"title": "First Rule CFamily", "status": "ready"}, f)

        # Add cfamily specialization for second rule
        cfamily2_dir = self.rules_dir / "S456" / "cfamily"
        cfamily2_dir.mkdir(parents=True)

        with open(cfamily2_dir / "rule.adoc", "w") as f:
            f.write(
                "= Second Rule CFamily\n\n== Description\n\nSecond rule cfamily description."
            )

        with open(cfamily2_dir / "metadata.json", "w") as f:
            json.dump({"title": "Second Rule CFamily", "status": "ready"}, f)

        # Run generate_html
        runner = CliRunner()
        result = runner.invoke(
            generate_html,
            ["--rules-dir", str(self.rules_dir), "--output-dir", str(self.output_dir)],
        )

        # Check command execution was successful
        assert result.exit_code == 0

        # Check all 4 HTML files were created
        expected_files = [
            self.output_dir / "S123" / "python" / "rule.html",
            self.output_dir / "S123" / "cfamily" / "rule.html",
            self.output_dir / "S456" / "python" / "rule.html",
            self.output_dir / "S456" / "cfamily" / "rule.html",
        ]

        for file_path in expected_files:
            assert file_path.exists(), f"Expected HTML file not found: {file_path}"

        # Check all 4 metadata files were copied
        expected_metadata_files = [
            self.output_dir / "S123" / "python" / "metadata.json",
            self.output_dir / "S123" / "cfamily" / "metadata.json",
            self.output_dir / "S456" / "python" / "metadata.json",
            self.output_dir / "S456" / "cfamily" / "metadata.json",
        ]

        for file_path in expected_metadata_files:
            assert file_path.exists(), f"Expected metadata file not found: {file_path}"

        # Check content of HTML files
        with open(expected_files[0], "r") as f:
            assert "Sample Rule Title" in f.read()

        with open(expected_files[1], "r") as f:
            assert "First Rule CFamily" in f.read()

        with open(expected_files[2], "r") as f:
            assert "Second Rule Python" in f.read()

        with open(expected_files[3], "r") as f:
            assert "Second Rule CFamily" in f.read()
