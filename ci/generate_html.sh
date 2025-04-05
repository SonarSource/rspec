#!/bin/bash
set -euo pipefail

# DEPRECATED: Please use the Python implementation:
# python -m rspec_tools.cli generate-html
# 
# This script is kept for backward compatibility

mkdir -p out
asciidoctor -R rules -D out 'rules/*/*/rule.adoc' -q
cd rules
find . -name 'metadata.json' -exec cp --parents '{}' ../out \;
cd ..
