#!/bin/bash
set -ueo pipefail

git fetch --quiet "${CIRRUS_DEFAULT_ORIGIN:-origin}" "${CIRRUS_DEFAULT_BRANCH:-master}"
base="$(git merge-base FETCH_HEAD HEAD)"
echo "Comparing against the merge-base: ${base}"
if ! git diff --name-only --exit-code "${base}" -- rspec-tools/
then
  # Revalidate all rules
  affected_rules="$(basename --multiple rules/*)"
else
  affected_rules="$(git diff --name-only "${base}" -- rules/ | sed -Ee 's#rules/(S[0-9]+)/.*#\1#' | sort -u)"
fi

# Turn affected_rules into an array, for proper handling of spaces:
# one line is one element in the array
readarray -t affected_rules < <(echo "${affected_rules}")

# Validate metadata
if [[ "${#affected_rules[@]}" -gt 0 ]]
then
  cd rspec-tools
  pipenv install
  pipenv run rspec-tools validate-rules-metadata "${affected_rules[@]}"
fi
