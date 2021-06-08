#!/bin/bash
set -uo pipefail

cd rspec-tools
pipenv install
cd ..

git fetch origin $CIRRUS_DEFAULT_BRANCH
BRANCH_BASE_SHA=$(git merge-base FETCH_HEAD HEAD)
echo "Comparing against the merge-base: $BRANCH_BASE_SHA"
changeset=$(git diff --name-only $BRANCH_BASE_SHA..HEAD)
affected_rules=$(printf '%s\n' "$changeset" | grep '/S[0-9]\+/' | sed 's:\(.*/S[0-9]\+\)/.*:\1:' | sort | uniq)
affected_tooling=$(printf '%s\n' "$changeset" | grep -v '/S[0-9]\+/')
if [ ! -z "$affected_tooling" ]; then
    echo "Some rpec tools are changed, validating all rules"
    affected_rules=rules/*
fi

./ci/generate_html.sh

cd rspec-tools
# validate sections in asciidoc
if pipenv run rspec-tools check-sections --d ../out; then
    echo "Sections are fine"
else
    echo "ERROR: incorrect section names"
    exit_code=1
fi
cd ..


exit_code=0

for dir in $affected_rules
do
  if [ ! -d "$dir" ]; then
    echo "apparently $dir is deleted, skipping"
    continue
  fi
  dir=${dir%*/}
  echo ${dir##*/}

  subdircount=$(find $dir -maxdepth 1 -type d | wc -l)

  # check if there are language specializations
  if [[ "$subdircount" -eq 1 ]]
  then
    # no specializations, that's fine if the rule is deprecated
    if grep -q '"status": "deprecated"\|"status": "closed"' "$dir/metadata.json"; then
      echo "INFO: deprecated generic rule $dir with no language specializations"
    else
      echo "ERROR: non-deprecated generic rule $dir with no language specializations"
      exit_code=1
    fi
  else
    #validate asciidoc
	supportedLanguages=$(sed 's/ or//' supported_languages.adoc | tr -d '`,')
	for language in $dir/*/
    do
      language=${language%*/}
      echo ${language##*/}
	  if [[ ! "${supportedLanguages[@]}" =~ "${language##*/}" ]]; then
	    echo "ERROR: ${language##*/} is not a supported language"
		exit_code=1
      fi
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
