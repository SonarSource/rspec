#!/bin/bash
set -euo pipefail

#setup python
pipenv install

#validate links in asciidoc
mkdir -p out
asciidoctor -R rules -D out '**/*.adoc' 
pipenv run python checklinks.py
