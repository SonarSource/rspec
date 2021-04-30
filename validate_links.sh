#!/bin/bash
set -euo pipefail

#validate links in asciidoc
cd rspec-tools
pipenv install -e .
pipenv run rspec-tools check-links --d ../out
