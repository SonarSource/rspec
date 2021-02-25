#!/bin/bash
set -euo pipefail

#validate links in asciidoc
mkdir -p out
asciidoctor -R rules -D out 'rules/**/*.adoc'
cd rspec-tools
pipenv install -e .
pipenv run rspec-tools check-links --d ../out