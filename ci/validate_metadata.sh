#!/bin/bash
set -ueo pipefail
shopt -s lastpipe # To pipe command result into mapfile and have the array variable available in the main shell process.

git fetch --quiet "${CIRRUS_DEFAULT_ORIGIN:-origin}" "${CIRRUS_DEFAULT_BRANCH:-master}"
base="$(git merge-base FETCH_HEAD HEAD)"
echo "Comparing against the merge-base: ${base}"
if ! git diff --name-only --exit-code "${base}" -- rspec-tools/
then
  basename --multiple rules/* | mapfile -t affected_rules
  echo "Change in the tools, revalidating all rules"
else
  git diff --name-only "${base}" -- rules/ | # Get all the changes in rules
    sed -Ee 's#(rules/S[0-9]+)/.*#\1#' | # extract the rule directories
    sort -u | # deduplicate
    while IFS= read -r rule; do [[ -d "$rule" ]] && echo "$rule" || true; done |  # filter non-deleted rules
    sed 's#rules/##' | # get rule ids
    mapfile -t affected_rules # store them in the `affected_rules` array
  echo "Validating ${affected_rules[@]}"
fi

# Validate metadata
if [[ "${#affected_rules[@]}" -gt 0 ]]
then
  cd rspec-tools
  pipenv install
  pipenv run rspec-tools validate-rules-metadata "${affected_rules[@]}"
else
  echo "No rule changed or added"
fi
