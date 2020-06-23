#!/bin/bash
echo "Test metadata.json"

exit_code=0

for dir in rules/*
do
    dir=${dir%*/} 
    echo ${dir##*/}
    if test -f "$dir/metadata.json"; then
      echo "$FILE exists."
      HAS_TITLE=`cat $dir/metadata.json | jq 'has("title")'`
      if [ "$HAS_TITLE" != "true" ]; then
        echo "$dir/metadata.json has no title"
        exit_code=1
      fi
    else
      echo "no $dir/metadata.json"
      exit_code=1
    fi
done

exit $exit_code
