#!/bin/bash
set -euo pipefail

#validate links in asciidoc
mkdir -p out
asciidoctor -R rules -D out '**/*.adoc' 
rspec-tools check-links --d out
