#!/usr/bin/env bash

set -euo pipefail

python --version

cd rspec-tools
pipenv run python --version
pipenv install --dev
#pipenv run pip install pytest pytest-cov
