#!/bin/sh

# Script reserving a RSPEC identifier.
# It is used by the Github Action script "create_new_rspec.yml".

# Stop script in case of error.
set -e

# Increment the next_id counter.
next_id=`cat next_rspec_id.txt`
new_next_id=`expr $next_id + 1`
echo $new_next_id > next_rspec_id.txt
git add next_rspec_id.txt
git commit "Increment RSPEC ID counter"
git push origin rspec-id-counter

# Set the Environment variable for the next Github Action.
echo "::set-env name RSPEC_ID=${next_id}"
