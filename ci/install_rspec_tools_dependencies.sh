#!/usr/bin/env bash

set -euo pipefail

python --version

cd rspec-tools
pipenv run python --version
pipenv install --dev
