for dir in rules/*
do
  dir=${dir%*/}
  echo ${dir##*/}
  #validate metadata
  FILE="$dir/metadata.json"
  if test -f $FILE; then
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
  else
    #validate asciidoc
    for language in $dir/*/
    do
      language=${language%*/}
      echo ${language##*/}
      RULE="$language/rule.adoc"
      if test -f $RULE; then
        echo "$RULE exists."
        TMP_ADOC="$language/tmp.adoc"
        echo "== Description" > $TMP_ADOC
        cat $RULE >> $TMP_ADOC
        if asciidoctor --failure-level=WARNING -o /dev/null $TMP_ADOC; then
          echo "$RULE syntax is fine"
        else
          echo "ERROR: $RULE has incorrect asciidoc"
          exit_code=1
        fi
        rm $TMP_ADOC
      else
        echo "ERROR: no asciidoc file $RULE"
        exit_code=1
      fi
    done
  fi
done

exit $exit_code