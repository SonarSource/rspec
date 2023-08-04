#!/usr/bin/env bash
#
# Run integration tests for ci/asciidoc_validation.

set -uo pipefail

# We could write complex checks to ensure only specific commands fail and emit
# a specific error message. Instead, we rely on `set -xe` to consistently and
# reliably exit with non-zero if any command fails and pinpoint which command
# failed in the trace output. We also use a trap on ERR to give users a short
# hint, and `set -E` to propagate this trap to shell functions and subshells.
#
# This allows use to write tests as simple commands, such as
#   test -f file_exists
#
# When we want to ensure a command fails, we use this pattern:
#   { ! command; }
set -xeE
err_trap() {
  set +x # Disable tracing when displaying stackframe.
  echo "Some test failed; look at the trace for more. Here is the stackframe:" >&2
  i=0
  while caller $i >&2
  do
    (( i++ )) || :
  done
}
trap err_trap ERR

# Ensure the script we test exists and is executable.
GIT_TOPLEVEL_DIR="$(git rev-parse --show-toplevel)"
VALIDATE_SCRIPT="${GIT_TOPLEVEL_DIR}/ci/asciidoc_validation/validate.sh"
test -f "${VALIDATE_SCRIPT}"
test -x "${VALIDATE_SCRIPT}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

run_test() {
  # Run validation script on $1.
  # Ensure the output contains $2...$N.
  tmp="$(mktemp -d)"
  stderr_log="${tmp}/stderr_log"
  stdout_log="${tmp}/stdout_log"
  if TOPLEVEL="${SCRIPT_DIR}/$1" "${VALIDATE_SCRIPT}" 2> "${stderr_log}" > "${stdout_log}"
  then
    # The validation succeeded. We expect nothing in the output.
    [ $# -eq 1 ] # no tests
    test -f "${stderr_log}"
    { ! test -s "${stderr_log}"; }
  else
    # We expect at least on check of the stderr content.
    [ $# -gt 1 ]
    shift

    for query in "$@"
    do
      test -n "${query}"
      grep -q -e "${query}" "${stderr_log}"
    done
  fi

  # Regardless of success or failure, the stdout is expected to be empty.
  test -f "${stdout_log}"
  { ! test -s "${stdout_log}"; }
}

run_test "test_valid"

run_test "test_unused_adoc" \
  "ERROR: These adoc files are not included anywhere:" \
  "rules/S100/java/unused.adoc" \
  "rules/S100/unused.adoc" \
  "shared_content/unused.adoc"

run_test "test_bad_cross_ref" \
  "ERROR: Some rules try to include content from unallowed directories." \
  "S100 cross-references .*rules/S1000/bad.adoc" \
  "S1000 cross-references .*rules/S100/java/bad.adoc"

run_test "test_diff_source" \
  "ERROR: Diff sources are incorrectly used:" \
  "\[S100/cfamily] diff-type is missing in .*/rules/S100/cfamily/rule.adoc:3" \
  "\[S100/cfamily] diff-id is missing in .*/rules/S100/cfamily/rule.adoc:8" \
  "\[S100/cfamily] diff-type 'bad' is not valid in .*/rules/S100/cfamily/rule.adoc:13" \
  "\[S100/cfamily] diff-type is missing in .*/rules/S100/cfamily/local.adoc:3" \
  "\[S100/cfamily] diff-id is missing in .*/rules/S100/cfamily/local.adoc:8" \
  "\[S100/cfamily] diff-type 'local' is not valid in .*/rules/S100/cfamily/local.adoc:13" \
  "\[S100/cfamily] diff-type is missing in .*/shared_content/cfamily/shared.adoc:3" \
  "\[S100/cfamily] diff-id is missing in .*/shared_content/cfamily/shared.adoc:8" \
  "\[S100/cfamily] diff-type 'shared' is not valid in .*/shared_content/cfamily/shared.adoc:13" \
  "\[S100/java] Incomplete example for diff-id=1, missing counterpart for .*/rules/S100/java/rule.adoc:3" \
  "\[S100/java] Incomplete example for diff-id=2, missing counterpart for .*/rules/S100/java/rule.adoc:8" \
  "\[S100/java] Incomplete example for diff-id=3, missing counterpart for .*/shared_content/java/example.adoc:3" \
  "\[S100/java] 3 examples for diff-id=4: .*/rules/S100/java/rule.adoc:15, .*/shared_content/java/example.adoc:13, .*/shared_content/java/example.adoc:8" \
  "\[S200/default] 3 examples for diff-id=1: .*/rules/S200/rule.adoc:12, .*/rules/S200/rule.adoc:2, .*/rules/S200/rule.adoc:7" \
  "\[S200/default] Two noncompliant examples for diff-id=2: .*/rules/S200/rule.adoc:17 and .*/rules/S200/rule.adoc:22"

echo "All tests passed"
