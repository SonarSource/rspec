#!/bin/bash
set -uo pipefail

# Install script dependencies
cd rspec-tools
pipenv install
cd ..

# Compute the set of affected rules
git fetch origin $CIRRUS_DEFAULT_BRANCH
branch_base_sha=$(git merge-base FETCH_HEAD HEAD)
echo "Comparing against the merge-base: $branch_base_sha"
changeset=$(git diff --name-only $branch_base_sha..HEAD)
affected_rules=$(printf '%s\n' "$changeset" | grep '/S[0-9]\+/' | sed 's:\(.*/S[0-9]\+\)/.*:\1:' | sort | uniq)
affected_tooling=$(printf '%s\n' "$changeset" | grep -v '/S[0-9]\+/')
if [ ! -z "$affected_tooling" ]; then
    echo "Some rpec tools are changed, validating all rules"
    affected_rules=rules/*
fi

rule_dir=$PWD

exit_code=0

./ci/generate_html.sh

cd rspec-tools
# validate sections in asciidoc
if pipenv run rspec-tools check-sections --d ../out; then
    echo "Sections are fine"
else
    echo "ERROR: incorrect section names or invalid level-0 headers"
    exit_code=1
fi
cd ..


for dir in $affected_rules
do
  if [ ! -d "$dir" ]; then
    echo "Apparently $dir is deleted, skipping"
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
            if asciidoctor -a rspecator-view --failure-level=WARNING -o /dev/null $TMP_ADOC; then
                echo "$RULE syntax is fine"
            else
                echo "ERROR: $RULE has incorrect asciidoc in rspecator-view mode"
                exit_code=1
            fi
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
    # Check that all adoc are included
    find $dir -name "*.adoc" -execdir sh -c 'grep -h "include::" {} | grep -v "rule.adoc" | sed "s/include::\(.*\)\[\]/\1/" | xargs -r -I@ realpath --relative-to=$rule_dir "$PWD/@"' \; > included
    find $dir -name "*.adoc" ! -name 'rule.adoc' -exec realpath --relative-to=$rule_dir {} \; > created
    orphans=comm -1 -3 <(sort included | uniq) <(sort created | uniq)
    if [ ! -z orphans ]; then
        echo "ERROR: These adoc files are not included anywhere:\n$orphans"
        exit_code=1
    fi
    rm included created
  fi
done

echo "Finished."
if (( $exit_code == 0 )); then
    echo "Success"
else
    echo "There were errors"
fi
exit $exit_code
