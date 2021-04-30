#!/bin/bash
set -euo pipefail

#validate links in asciidoc
mkdir -p out
asciidoctor -R rules -D out 'rules/*/*/rule.adoc'
cd rules
  find . -name 'metadata.json' -exec cp --parents '{}' ../out \;
cd ..
cd rspec-tools
pipenv install -e .
pipenv run rspec-tools check-links --d ../out
