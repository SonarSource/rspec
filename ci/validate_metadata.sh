#!/bin/bash
set -ueo pipefail
shopt -s lastpipe # To pipe command result into mapfile and have the array variable available in the main shell process.

git fetch --quiet "${CIRRUS_DEFAULT_ORIGIN:-origin}" "${CIRRUS_DEFAULT_BRANCH:-master}"
base="$(git merge-base FETCH_HEAD HEAD)"
echo "Comparing against the merge-base: ${base}"
if ! git diff --name-only --exit-code "${base}" -- rspec-tools/
then
  # Revalidate all rules
  basename --multiple rules/* | mapfile -t affected_rules
else
  git diff --name-only "${base}" -- rules/ | sed -Ee 's#rules/(S[0-9]+)/.*#\1#' | sort -u | mapfile -t affected_rules
fi

# Validate metadata
if [[ "${#affected_rules[@]}" -gt 0 ]]
then
  cd rspec-tools
  pipenv install
  pipenv run rspec-tools validate-rules-metadata "${affected_rules[@]}"
fi
