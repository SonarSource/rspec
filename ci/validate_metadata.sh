#!/bin/bash
set -ueo pipefail

invalid=0

# Validate metadata
cd rspec-tools
pipenv install
pipenv run rspec-tools validate-rules-metadata || invalid=1

exit "${invalid}"