#!/bin/bash

set -euo pipefail

echo CIRRUS_BASE_BRANCH: $CIRRUS_BASE_BRANCH
echo CIRRUS_DEFAULT_BRANCH: $CIRRUS_DEFAULT_BRANCH
echo CIRRUS_REPO_CLONE_URL: $CIRRUS_REPO_CLONE_URL

# When neither CIRRUS_BASE_BRANCH nor CIRRUS_DEFAULT_BRANCH are defined, fall back to "master".
BRANCH="${CIRRUS_BASE_BRANCH:-${CIRRUS_DEFAULT_BRANCH:-master}}"
git fetch "${CIRRUS_REPO_CLONE_URL}" "+refs/heads/${BRANCH}:refs/remotes/origin/${BRANCH}"
