#!/bin/bash
set -uo pipefail

readonly ALLOWED_RULE_SUB_FOLDERS=['common'];

# Install script dependencies
cd rspec-tools
pipenv install
cd ..

# Compute the set of affected rules
git fetch origin "$CIRRUS_DEFAULT_BRANCH"
branch_base_sha=$(git merge-base FETCH_HEAD HEAD)
echo "Comparing against the merge-base: $branch_base_sha"
changeset=$(git diff --name-only "$branch_base_sha"..HEAD)
affected_rules=$(printf '%s\n' "$changeset" | grep '/S[0-9]\+/' | sed 's:\(.*/S[0-9]\+\)/.*:\1:' | sort | uniq)
affected_tooling=$(printf '%s\n' "$changeset" | grep -v '/S[0-9]\+/')
if [ -n "$affected_tooling" ]; then
    echo "Some rpec tools are changed, validating all rules"
    affected_rules=rules/*
fi

exit_code=0

./ci/generate_html.sh

PATH_WITH_VARIABLE="$(realpath ./ci/replace_variables_in_path.sh)"

cd rspec-tools
if pipenv run rspec-tools check-description --d ../out; then
    echo "rule.adoc is fine"
else
    echo "ERROR: There are invalid rule.adoc"
    exit_code=1
fi
cd ..

echo "Testing the following rules: ${affected_rules}"

readonly ROOT=$PWD

for dir in $affected_rules
do
  if [ ! -d "$dir" ]; then
    echo "Apparently $dir is deleted, skipping"
    continue
  fi
  dir=${dir%*/}

  subdircount=$(find "$dir" -maxdepth 1 -type d | wc -l)

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

    # Make sure include:: clauses are always more than one line away from the previous content
    # Detect includes stuck to the line before
    find "$dir" -name "*.adoc" -execdir sh -c 'grep -Pzl "\S[ \t]*\ninclude::" $1  | xargs -r -I@ realpath "$PWD/@"' shell {} \; > stuck
    # Detect includes stuck to the line after
    find "$dir" -name "*.adoc" -execdir sh -c 'grep -Pzl "include::[^\[]+\[\]\n[ \t]*[^\n]" $1  | xargs -r -I@ realpath "$PWD/@"' shell {} \; >> stuck
    if [ -s stuck ]; then
        echo "ERROR: These adoc files contain an include that is stuck to other content."
        echo "This may result in broken tags and other display issues."
        echo "Make sure there is an empty line before and after each include:"
        cat stuck
        exit_code=1
    fi
    rm -f stuck

    supportedLanguages=$(sed 's/ or//' supported_languages.adoc | tr -d '`,')
    for language in $dir/*/
    do
      language=${language%*/}
      if [[ ! "${supportedLanguages[*]}" == *"${language##*/}"* ]]; then
        if [[ ! "${ALLOWED_RULE_SUB_FOLDERS[*]}" == *"${language##*/}"* ]]; then
          echo "ERROR: ${language##*/} is not a supported language"
          exit_code=1
        fi
      else
        RULE="$language/rule.adoc"
        if test -f "$RULE"; then
          # We build this filename that describes the path to workaround the fact that asciidoctor will not tell
          # us the path of the file in case of error.
          # We can remove it if https://github.com/asciidoctor/asciidoctor/issues/3414 is fixed.
          TMP_ADOC="$language/tmp_$(basename "${dir}")_${language##*/}.adoc"
          echo "== Description" > "$TMP_ADOC"
          cat "$RULE" >> "$TMP_ADOC"
        else
          echo "ERROR: no asciidoc file $RULE"
          exit_code=1
        fi
      fi
    done

    # Check that all adoc are included

    # Files can be included through variables. We create a list of variables
    # These paths are relative to the file where they are _included_, not where they are _declared_
    # Which is why we need to create this list and cannot do anything with the paths it contains until we find the corresponding include
    find "$dir" -name "*.adoc" ! -name 'tmp_*.adoc' -execdir sed -r -n -e 's/^:(\w+):\s+([A-Za-z0-9\/._-]+)$/\1\t\2/p' {} \; > vars
    # Directly included
    find "$dir" -name "*.adoc" ! -name 'tmp_*.adoc' -execdir sh -c 'grep -h "include::" "$1" | grep -Ev "{\w+}" | grep -v "rule.adoc" | sed -r "s/include::(.*)\[\]/\1/" | xargs -r -I@ realpath "$PWD/@"' shell {} \; > included
    # Included through variable
    VARS_FULL_PATH=$(realpath vars) PATH_WITH_VARIABLE=${PATH_WITH_VARIABLE} find "$dir" ! -name 'tmp_*.adoc' -name "*.adoc" -execdir sh -c 'grep -Eh "include::.*\{" "$1" | xargs -r -I@ $PATH_WITH_VARIABLE $VARS_FULL_PATH "@" | xargs -r -I@ realpath "$PWD/@"' shell {} \; >> included
    # We should only include documents from the same rule or from shared_content
    cross_references=$(grep -vEh "${ROOT}\/${dir}\/|${ROOT}\/shared_content\/" included)
    if [[ -n "$cross_references" ]]; then
        printf 'ERROR: Rule %s tries to include content from unallowed directory:\n%s\nTo share content between rules, you should use the "shared_content" folder at the root of the repository\n' "$dir" "$cross_references"
        exit_code=1
    fi
    find "$dir" -name "*.adoc" ! -name 'rule.adoc' ! -name 'tmp*.adoc' -exec sh -c 'realpath $1' shell {} \; > created
    orphans=$(comm -1 -3 <(sort -u included) <(sort -u created))
    if [[ -n "$orphans" ]]; then
        printf 'ERROR: These adoc files are not included anywhere:\n-----\n%s\n-----\n' "$orphans"
        exit_code=1
    fi
    rm -f included created vars
  fi
done

ADOC_COUNT=$(find rules -name "tmp*.adoc" | wc -l)

if (( ADOC_COUNT > 0 )); then
  if asciidoctor --failure-level=WARNING -o /dev/null rules/*/*/tmp*.adoc; then
      if asciidoctor -a rspecator-view --failure-level=WARNING -o /dev/null rules/*/*/tmp*.adoc; then
          echo "${ADOC_COUNT} documents checked with success"
      else
          echo "ERROR: malformed asciidoc files in rspecator-view"
          exit_code=1
      fi
  else
    echo "ERROR: malformed asciidoc files"
    exit_code=1
  fi
else
  echo "No new asciidoc file changed"
fi

find rules -name "tmp*.adoc" -delete

if (( exit_code == 0 )); then
    echo "Success"
else
    echo "There were errors"
fi
exit $exit_code
