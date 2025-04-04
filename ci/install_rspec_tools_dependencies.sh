#!/usr/bin/env bash

set -euo pipefail

pip install wheel
cd rspec-tools
pipenv install --dev
pipenv run pip install pytest pytest-cov
