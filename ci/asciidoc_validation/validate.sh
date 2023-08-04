#!/usr/bin/env bash
#
# Validate file inclusion and cross-references.
#
# This script is parametrized by this environment variable:
#  * TOPLEVEL: $TOPLEVEL/rules and $TOPLEVEL/shared_content will be validated.
#
# The script exists with a non-zero value when an unexpected error happened or
# there are asciidoc validation errors.
#
# Validation errors are reported on stderr.
#
# Implementation details:
#
#   The validation of file inclusion and cross-references needs to be done
#   on all rule descriptions, including the default, language-agnostic
#   description, with rspecator-view. Otherwise, a rule could drop an include
#   of a shared_content asciidoc and that file could become unused.
#
#   We use a custom asciidoctor with extra logging for this purpose.
#   The format for the interesting log entries are:
#     asciidoctor: INFO: ASCIIDOC LOGGER MAIN FILE: $PATH
#     asciidoctor: INFO: ASCIIDOC LOGGER INCLUDED: $PATH
#     asciidoctor: INFO: ASCIIDOC LOGGER CROSSREFERENCE: $RULEID cross-references $PATH

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
TOPLEVEL="$(realpath "${TOPLEVEL}")"
RULES_DIR="${TOPLEVEL}/rules"
SHARED_CONTENT_DIR="${TOPLEVEL}/shared_content"
TMPOUT_DIR="$(mktemp -d)"

exit_code=0

grep_nofail() {
  # Grep but always exit with 0 when there are no matches.
  # Yet, exit with non-zero if an error occured.
  grep "$@" || [ "$?" == "1" ]
}

find "${RULES_DIR}" -name 'rule.adoc' \
  | xargs "${SCRIPT_DIR}/custom-asciidoctor" -a rspecator-view --verbose -R "${RULES_DIR}" -D "${TMPOUT_DIR}" 2>&1 \
  | grep_nofail -e 'ASCIIDOC LOGGER' \
  > "${TMPOUT_DIR}/asciidoc_introspection"

grep -ve 'CROSSREFERENCE' "${TMPOUT_DIR}/asciidoc_introspection" \
  | cut -d ':' -f 4 \
  | sort -u \
  > "${TMPOUT_DIR}/used_asciidoc_files"

git ls-files --cached -- "${RULES_DIR}/**.adoc" "${SHARED_CONTENT_DIR}/**.adoc" \
  | xargs realpath \
  > "${TMPOUT_DIR}/all_asciidoc_files"

cross_references=$(grep_nofail -e 'CROSSREFERENCE' "${TMPOUT_DIR}/asciidoc_introspection" | cut -d ':' -f 4 | sort -u)
if [[ -n "$cross_references" ]]; then
  echo >&2 'ERROR: Some rules try to include content from unallowed directories.'
  echo >&2 'To share content between rules, you should use the "shared_content" folder at the root of the repository.'
  echo >&2 'List of errors:'
  echo >&2 "${cross_references}"
  exit_code=1
fi

orphans=$(comm -1 -3 <(sort -u "${TMPOUT_DIR}/used_asciidoc_files") <(sort -u "${TMPOUT_DIR}/all_asciidoc_files"))
if [[ -n "$orphans" ]]; then
  printf >&2 'ERROR: These adoc files are not included anywhere:\n-----\n%s\n-----\n' "$orphans"
  exit_code=1
fi

exit $exit_code
