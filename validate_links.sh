#!/bin/bash
set -euo pipefail

CACHE_PATH=$1
echo "CACHE_PATH: $CACHE_PATH"
[ ! -d $CACHE_PATH ] && mkdir $CACHE_PATH
ls -al $CACHE_PATH

[ -f "$CACHE_PATH/link_probes.history" ] && cp "$CACHE_PATH/link_probes.history" ./

./generate_html.sh

#validate links in asciidoc
cd rspec-tools
pipenv install -e .
pipenv run rspec-tools check-links --d ../out

cp ./link_probes.history "$CACHE_PATH/"
