#!/usr/bin/env bash

set -euo pipefail

TOP_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)/..

$TOP_DIR/ci/install_rspec_tools_dependencies.sh
