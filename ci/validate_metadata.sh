#!/bin/bash
set -x
set -ueo pipefail

invalid=0

git fetch --quiet "${CIRRUS_DEFAULT_ORIGIN:-origin}" "${CIRRUS_DEFAULT_BRANCH:-master}"
base="$(git merge-base FETCH_HEAD HEAD)"
modifiedRules="$(git diff --name-only "${base}" -- rules | sed -Ee 's#rules/(S[0-9]+)/.*#\1#' | sort -u)"

cd rspec-tools

# Validate new and modified rules' metadata
for rule in ${modifiedRules}
do
  pipenv run rspec-tools validate-modified-rule-metadata "${rule}" || invalid=1
done

# Validate all metadata
pipenv install
pipenv run rspec-tools validate-rules-metadata || invalid=1

exit "${invalid}"