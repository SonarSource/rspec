#!/bin/bash
set -euo pipefail

./generate_html.sh

#validate links in asciidoc
cd rspec-tools
pipenv install -e .
pipenv run rspec-tools check-links --d ../out
