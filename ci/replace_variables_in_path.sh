#!/bin/bash

set -uo pipefail

BEFORE=$(echo "$2" | sed -r "s/include::(.*)\{(.*)\}(.*)\[\]/\1/")
VAR=$(echo "$2" | sed -r "s/include::(.*)\{(.*)\}(.*)\[\]/\2/")
AFTER=$(echo "$2" | sed -r "s/include::(.*)\{(.*)\}(.*)\[\]/\3/")

grep "${VAR}" "$1" | cut -f2 | xargs -I@ echo "${BEFORE}@${AFTER}"
