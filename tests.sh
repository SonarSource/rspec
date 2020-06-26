#!/bin/bash
set -euo pipefail
echo "Test metadata.json"

exit_code=0

for dir in rules/*
do
    dir=${dir%*/} 
    echo ${dir##*/}
    FILE="$dir/metadata.json"
    if test -f $FILE; then
      echo "$FILE exists."
      validate-json $FILE ./validation/schema.json       
    else
      echo "no $FILE"
      exit_code=1
    fi
done

exit $exit_code
