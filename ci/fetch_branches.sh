#!/bin/bash

set -euo pipefail

echo "SCRIPT DEBUG..."

echo "BASE_BRANCH: $BASE_BRANCH"
echo "DEFAULT_BRANCH: $DEFAULT_BRANCH"
echo "REPO_CLONE_URL: $REPO_CLONE_URL"

# When neither BASE_BRANCH nor DEFAULT_BRANCH are defined, fall back to "master".
BRANCH="${BASE_BRANCH:-${DEFAULT_BRANCH:-master}}"
git fetch "${REPO_CLONE_URL}" "+refs/heads/${BRANCH}:refs/remotes/origin/${BRANCH}"
