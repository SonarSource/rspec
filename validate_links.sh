#!/bin/bash
set -euo pipefail

#setup python
cd rspec-tools
pipenv install -e i
pipenv shell
cd ..

#validate links in asciidoc
mkdir -p out
asciidoctor -R rules -D out '**/*.adoc' 
rspec-tools check-links --d out
