#!/bin/bash
set -euo pipefail

mkdir -p out
asciidoctor -R rules -D out 'rules/*/*/rule.adoc'
cd rules
find . -name 'metadata.json' -exec cp --parents '{}' ../out \;
cd ..
