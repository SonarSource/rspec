#!/bin/bash
set -euo pipefail

#validate asciidoc
find rules -type f -name "*.adoc" | while read line; do
  if ! asciidoctor --failure-level=WARNING -o /dev/null $line; then    
    echo "ERROR: $line has incorrect asciidoc"
    exit_code=1
  fi
done
exit $exit_code