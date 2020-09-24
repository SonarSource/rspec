#!/bin/sh

# Script reserving a RSPEC identifier.
# It is used by the Github Action script "create_new_rspec.yml".

# Stop script in case of error.
set -e

RSPEC_ID_COUNTER_FILE=$1

# Increment the next_id counter.
next_id=`cat ${RSPEC_ID_COUNTER_FILE}`
new_next_id=`expr $next_id + 1`
echo $new_next_id > ${RSPEC_ID_COUNTER_FILE}
git add ${RSPEC_ID_COUNTER_FILE}
git commit -m "Increment RSPEC ID counter"
git push origin rspec-id-counter

# Set the Environment variable for the next Github Action.
echo "::set-env name=RSPEC_ID::${next_id}"
