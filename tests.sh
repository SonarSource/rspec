#!/bin/bash
echo "Test metadata.json"

exit_code=0

for dir in rules/*
do
    dir=${dir%*/} 
    echo ${dir##*/}
    FILE="$dir/metadata.json"
    if test -f $FILE; then
      echo "$FILE exists."
      HAS_TITLE=`cat $FILE | jq 'has("title")'`
      if [ "$HAS_TITLE" != "true" ]; then
        echo "$FILE has no title"
        exit_code=1
      fi
    else
      echo "no $FILE"
      exit_code=1
    fi
done

exit $exit_code
