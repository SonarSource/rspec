import json
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase

import pytest
from click.testing import CliRunner

from rspec_tools.cli import generate_html  # Keep using the CLI function for testing


class TestGenerateHtml(TestCase):
    def setUp(self):
        # Create temporary directories for test
        self.test_dir = tempfile.mkdtemp()
        self.rules_dir = Path(self.test_dir) / "rules"
        self.output_dir = Path(self.test_dir) / "output"

        # Create the base directories
        self.rules_dir.mkdir(parents=True)
        self.output_dir.mkdir(parents=True)

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)

    def _create_rule(self, rule_id, language, title, content, metadata):
        """Helper method to create a rule directory with content"""
        rule_dir = self.rules_dir / rule_id / language
        rule_dir.mkdir(parents=True, exist_ok=True)

        # Create rule.adoc file
        rule_adoc = rule_dir / "rule.adoc"
        with open(rule_adoc, "w") as f:
            f.write(content)

        # Create metadata.json file
        metadata_json = rule_dir / "metadata.json"
        with open(metadata_json, "w") as f:
            json.dump(metadata, f)

        return rule_dir, rule_adoc, metadata_json

    def test_generate_html(self):
        """Test that generate_html produces the expected output files."""
        # Create a single rule
        rule_content = """= Sample Rule Title
            
== Description

This is a sample rule with a [link](https://example.com).
"""
        metadata = {
            "title": "Sample Rule",
            "type": "CODE_SMELL",
            "status": "ready",
            "remediation": {"func": "Constant/Issue", "constantCost": "5min"},
            "tags": ["example"],
            "defaultSeverity": "Major",
        }

        _, _, metadata_json = self._create_rule(
            "S123", "python", "Sample Rule", rule_content, metadata
        )

        # Run the command
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

        with open(metadata_json, "r") as f:
            original_metadata = json.load(f)

        assert copied_metadata == original_metadata, "Metadata files don't match"

    def test_generate_html_multiple_rules(self):
        """Test that generate_html processes multiple rules with multiple language specializations."""
        # Create first rule - python
        self._create_rule(
            "S123",
            "python",
            "Sample Rule",
            """= Sample Rule Title
            
== Description

This is a sample rule with a [link](https://example.com).
""",
            {
                "title": "Sample Rule",
                "type": "CODE_SMELL",
                "status": "ready",
                "tags": ["example"],
            },
        )

        # Create second rule - python
        self._create_rule(
            "S456",
            "python",
            "Second Rule Python",
            "= Second Rule Python\n\n== Description\n\nSecond rule python description.",
            {"title": "Second Rule Python", "status": "ready"},
        )

        # Create first rule - cfamily
        self._create_rule(
            "S123",
            "cfamily",
            "First Rule CFamily",
            "= First Rule CFamily\n\n== Description\n\nFirst rule cfamily description.",
            {"title": "First Rule CFamily", "status": "ready"},
        )

        # Create second rule - cfamily
        self._create_rule(
            "S456",
            "cfamily",
            "Second Rule CFamily",
            "= Second Rule CFamily\n\n== Description\n\nSecond rule cfamily description.",
            {"title": "Second Rule CFamily", "status": "ready"},
        )

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

    def test_generate_html_with_includes(self):
        """Test that generate_html correctly processes rule.adoc files that include other .adoc files."""
        # Create rule directory structure with shared .adoc files
        rule_id = "S789"
        rule_dir = self.rules_dir / rule_id
        rule_dir.mkdir(parents=True, exist_ok=True)

        # Create shared .adoc files in the rule base directory
        shared_description = rule_dir / "description.adoc"
        with open(shared_description, "w") as f:
            f.write(
                "This is a shared description that will be included in language-specific rule files."
            )

        shared_message = rule_dir / "message.adoc"
        with open(shared_message, "w") as f:
            f.write("This is a shared message for all languages.")

        shared_comments = rule_dir / "comments-and-links.adoc"
        with open(shared_comments, "w") as f:
            f.write("See also: RSPEC-123, S456")

        # Create rule metadata in base directory
        base_metadata = {
            "title": "Base Rule Title",
            "type": "CODE_SMELL",
            "status": "ready",
            "tags": ["example"],
        }
        with open(rule_dir / "metadata.json", "w") as f:
            json.dump(base_metadata, f)

        # Create Java specialization that includes the shared files
        java_dir = rule_dir / "java"
        java_dir.mkdir(parents=True, exist_ok=True)

        # Java rule.adoc that includes the shared files
        java_rule_content = """= Java Rule Title
        
== Description

include::../description.adoc[]

== How to fix

include::../message.adoc[]

== See also

include::../comments-and-links.adoc[]
"""

        with open(java_dir / "rule.adoc", "w") as f:
            f.write(java_rule_content)

        # Java-specific metadata
        java_metadata = {
            "title": "Java Rule Title",
            "status": "ready",
            "sqKey": "JavaRuleS789",
        }
        with open(java_dir / "metadata.json", "w") as f:
            json.dump(java_metadata, f)

        # Create Python specialization that also includes the shared files
        python_dir = rule_dir / "python"
        python_dir.mkdir(parents=True, exist_ok=True)

        # Python rule.adoc with includes
        python_rule_content = """= Python Rule Title
        
== Description

include::../description.adoc[]

== How to fix

include::../message.adoc[]

== See also

include::../comments-and-links.adoc[]
"""

        with open(python_dir / "rule.adoc", "w") as f:
            f.write(python_rule_content)

        # Python-specific metadata
        python_metadata = {
            "title": "Python Rule Title",
            "status": "ready",
            "sqKey": "PythonRuleS789",
        }
        with open(python_dir / "metadata.json", "w") as f:
            json.dump(python_metadata, f)

        # Run generate_html
        runner = CliRunner()
        result = runner.invoke(
            generate_html,
            ["--rules-dir", str(self.rules_dir), "--output-dir", str(self.output_dir)],
        )

        # Check command execution was successful
        assert result.exit_code == 0

        # Check both language HTML files were created
        java_html = self.output_dir / rule_id / "java" / "rule.html"
        python_html = self.output_dir / rule_id / "python" / "rule.html"

        assert java_html.exists(), f"Expected Java HTML file not found: {java_html}"
        assert (
            python_html.exists()
        ), f"Expected Python HTML file not found: {python_html}"

        # Check Java HTML content includes the shared content
        with open(java_html, "r") as f:
            java_content = f.read()
            assert "Java Rule Title" in java_content
            assert "This is a shared description" in java_content
            assert "This is a shared message" in java_content
            assert "See also: RSPEC-123, S456" in java_content

        # Check Python HTML content includes the shared content
        with open(python_html, "r") as f:
            python_content = f.read()
            assert "Python Rule Title" in python_content
            assert "This is a shared description" in python_content
            assert "This is a shared message" in python_content
            assert "See also: RSPEC-123, S456" in python_content

        # Verify metadata files are copied correctly
        java_metadata_out = self.output_dir / rule_id / "java" / "metadata.json"
        python_metadata_out = self.output_dir / rule_id / "python" / "metadata.json"
        base_metadata_out = self.output_dir / rule_id / "metadata.json"

        assert java_metadata_out.exists()
        assert python_metadata_out.exists()
        assert base_metadata_out.exists()
