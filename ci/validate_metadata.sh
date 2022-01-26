#!/bin/bash
set -ueo pipefail

exit_code=0

git fetch --quiet "${CIRRUS_DEFAULT_ORIGIN:-origin}" "${CIRRUS_DEFAULT_BRANCH:-master}"
base="$(git merge-base FETCH_HEAD HEAD)"
echo "Comparing against the merge-base: ${base}"
modified_rules="$(git diff --name-only "${base}" -- rules | sed -Ee 's#rules/(S[0-9]+)/.*#\1#' | sort -u)"

cd rspec-tools
pipenv install

# Validate all metadata
pipenv run rspec-tools validate-rules-metadata || exit_code=1

# Validate new or modified rules' metadata
for rule in ${modified_rules}
do
  pipenv run rspec-tools validate-modified-rule-metadata "${rule}" || exit_code=1
done

exit "${exit_code}"