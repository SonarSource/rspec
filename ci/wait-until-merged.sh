#!/bin/bash

set +uexo pipefail

# Implicitly referring to the PR corresponding to current branch

# Set timeout (20 minutes in seconds)
TIMEOUT=1200
START_TIME=$(date +%s)

while true; do
  # Check if the PR is merged
  PR_STATE=$(gh pr view --json state,mergedAt -q '.state')
  MERGED_AT=$(gh pr view --json state,mergedAt -q '.mergedAt')

  if [[ "${PR_STATE}" == "MERGED" ]]; then
    echo "PR merged at: $MERGED_AT"
    exit 0
  fi

  # Check for timeout
  CURRENT_TIME=$(date +%s)
  ELAPSED_TIME=$((CURRENT_TIME - START_TIME))

  if [[ "${ELAPSED_TIME}" -gt "${TIMEOUT}" ]]; then
    echo "Timeout waiting for PR to merge."
    exit 1
  fi

  # Wait for 30 seconds before checking again
  sleep 30
done
