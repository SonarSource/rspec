#!/bin/bash
set -euo pipefail
exit_code=0

#setup python
pipenv install

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
    echo "ERROR: no metadata file $FILE"
    exit_code=1
  fi
  subdircount=$(find $dir -maxdepth 1 -type d | wc -l)

  # check if there are language specializations
  if [[ "$subdircount" -eq 1 ]]
  then
    # no specializations, that's fine if the rule is deprecated
    if grep -q '"status": "deprecated"' "$dir/metadata.json"; then
        echo "INFO: deprecated generic rule $dir with no language specializations"
    else
        echo "ERROR: non-deprecated generic rule $dir with no language specializations"
        exit_code=1
    fi
  fi
done


#vaidate asciidoc
mkdir -p out
asciidoctor -R rules -D out '**/*.adoc'
pipenv run python checklinks.py

exit $exit_code
