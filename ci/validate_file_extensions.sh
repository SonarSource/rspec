#!/bin/bash
set -euxo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
TOPLEVEL="$(realpath "${TOPLEVEL}")"
RULES_DIR="${TOPLEVEL}/rules"

CS_FILES=$(find "${RULES_DIR}" -type f -name "*.cs")
VB_FILES=$(find "${RULES_DIR}" -type f -name "*.vb")

if [[ ${#CS_FILES[@]} -gt 0 ]] || [[ ${#VB_FILES[@]} -gt 0 ]]; then
    echo "ERROR: '.cs' and/or '.vb' files are detected."
    echo $CS_FILES
    echo $VB_FILES
    exit 1
fi
echo "SUCCESS: no '.cs' or '.vb' files detected."
exit 0