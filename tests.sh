#!/bin/bash
set -euo pipefail
exit_code=0

for dir in rules/*
do
  dir=${dir%*/} 
  echo ${dir##*/}
  #validate metadata
  FILE="$dir/metadata.json"
  if test -f $FILE; then
    echo "$FILE exists."
    validate-json $FILE ./validation/schema.json       
  else
    echo "no $FILE"
    exit_code=1
  fi
  #validate asciidoc 
  for language in $dir/*/
  do
    language=${language%*/} 
    echo ${language##*/}
    #validate metadata
    RULE="$language/rule.adoc"
    if test -f $RULE; then
      echo "$RULE exists."
      asciidoctor --failure-level=WARNING -o /dev/null $RULE      
    else
      echo "no $RULE"
      exit_code=1
    fi
    #validate asciidoc 

  done
done

exit $exit_code
