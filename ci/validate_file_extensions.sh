#!/bin/bash
set -euxo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
TOPLEVEL="$(realpath "${TOPLEVEL}")"
RULES_DIR="${TOPLEVEL}/rules"

CSVB_FILES=$(find "${RULES_DIR}" -type f -name "*.cs" -o -name "*.vb")

if [[ ${#CSVB_FILES[@]} -gt 0 ]]; then
    echo "ERROR: '.cs' and/or '.vb' files are detected."
    echo $CSVB_FILES
    exit 1
else 
    echo "SUCCESS: no '.cs' or '.vb' files detected."
    exit 0
fi