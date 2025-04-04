#!/usr/bin/env bash

set -euo pipefail

apt-get install gcc libpq-dev -y
apt-get install python-dev  python-pip -y
apt-get install python3-dev python3-pip python3-venv python3-wheel -y
pip3 install wheel

cd rspec-tools
pipenv install --dev
pipenv run pip install pytest pytest-cov
