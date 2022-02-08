#!/bin/bash

set -euo pipefail

# When neither BASE_BRANCH nor DEFAULT_BRANCH are defined, fall back to "master".
BRANCH="${BASE_BRANCH:-${DEFAULT_BRANCH:-master}}"
git fetch --force --all --prune
