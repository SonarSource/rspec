#!/usr/bin/env bash

set -euo pipefail

cd rspec-tools
pipenv install --dev
pipenv run pip install pytest pytest-cov
