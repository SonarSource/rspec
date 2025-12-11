#!/bin/bash
set -euxo pipefail

CACHE_PATH=$1
echo "CACHE_PATH: $CACHE_PATH"
[ ! -d $CACHE_PATH ] && mkdir $CACHE_PATH
ls -al $CACHE_PATH

if [ -f "$CACHE_PATH/link_probes.history" ]; then
  cp "$CACHE_PATH/link_probes.history" ./rspec-tools/
  du -hs "$CACHE_PATH/link_probes.history"
fi

./ci/generate_html.sh

# validate the links in asciidoc
cd rspec-tools
if pipenv install && pipenv run rspec-tools check-links --d ../out --history-file ./link_probes.history ; then
    EXIT_CODE=0
else
    EXIT_CODE=1
fi
cd ..

du -hs ./rspec-tools/link_probes.history
cp ./rspec-tools/link_probes.history "$CACHE_PATH/"

exit $EXIT_CODE
