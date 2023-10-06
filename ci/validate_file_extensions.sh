#!/bin/bash
#
# Validates that there are no files with .cs, .vb, .razor or .cshtml extensions present inside rules folder.
#
# As part of the new DotNet squad rule specification sprint guidelines, test case files similar to the ones 
# used for unit tests in sonar-dotnet should be temporarely added under the rule folder on RSPEC repository. 
# Those files can be of any number for both C# (*.cs, *.razor, *.cshtml) and VB.NET (.*vb).
# The test case files will be copied to the sonar-dotnet repository during the initial phases of implementation 
# and will serve as an initial test bed.
# Before merging the PR on the RSPEC side, it is important to ensure that these test case files are deleted.
# The script make sure to fail the CI if any of those previously mentioned files are present inside the rules folder.
set -euxo pipefail

TOPLEVEL="$(realpath .)"
RULES_DIR="${TOPLEVEL}/rules"
CSVB_FILES=($(find "${RULES_DIR}" -type f -name "*.cs" -o -name "*.vb" -o -name "*.razor" -o -name "*.cshtml"))

if [ ${#CSVB_FILES[@]} -gt 0 ]; then
    echo "ERROR: '.cs','.vb','.razor' or '.cshtml' files are detected."
    printf '%s\n' "${CSVB_FILES[@]}"
    exit 1
else 
    echo "SUCCESS: no '.cs' or '.vb' files detected."
    exit 0
fi