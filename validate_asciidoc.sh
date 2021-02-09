#!/bin/bash
set -euo pipefail

#validate asciidoc
find rules -type f -name "*.adoc" | while read line; do
  #in order to not fail for rspecs that have third-level headers in the description we always add a description
  TMP_ADOC="tmp.adoc"
  echo "== Description" > $TMP_ADOC
  cat $line >> $TMP_ADOC
  if ! asciidoctor --failure-level=WARNING -o /dev/null $TMP_ADOC; then    
    echo "ERROR: $line has incorrect asciidoc"
    exit_code=1
  fi
  rm $TMP_ADOC
done
exit $exit_code