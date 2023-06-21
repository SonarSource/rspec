#!/bin/bash
set -uoe pipefail

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 VARS_FILE INCLUDE_TEXT"
    echo "  This script should be called by validate_asciidoc.sh."
    echo "  When provided with an include that contains one variable part, will"
    echo "       output all possible values for this include."
    echo ""
    echo "  VARS_FILE:    a text file listing all variables as \"name\tvalue\""
    echo ""
    echo "  INCLUDE_TEXT: the whole include declaration"
    exit 1
fi

if echo "$2" | grep -Eq "\{.*\{" ; then
    echo "Multiple variables detected in \"$2\" this is not supported"
    exit 2
fi

BEFORE=$(echo "$2" | sed -r "s/include::(.*)\{(.*)\}(.*)\[\]/\1/")
VAR=$(echo "$2"    | sed -r "s/include::(.*)\{(.*)\}(.*)\[\]/\2/")
AFTER=$(echo "$2"  | sed -r "s/include::(.*)\{(.*)\}(.*)\[\]/\3/")

grep "${VAR}" "$1" | cut -f2 | xargs -I@ echo "${BEFORE}@${AFTER}"
