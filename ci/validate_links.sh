#!/bin/bash
set -euxo pipefail

CACHE_PATH=$1
echo "CACHE_PATH: $CACHE_PATH"
[ ! -d $CACHE_PATH ] && mkdir $CACHE_PATH
ls -al $CACHE_PATH

[ -f "$CACHE_PATH/link_probes.history" ] && cp "$CACHE_PATH/link_probes.history" ./rspec-tools/

./ci/generate_html.sh

# validate the links in asciidoc
cd rspec-tools
echo "start testing"
EXIT_CODE=2
if pipenv install && pipenv run rspec-tools check-links --d ../out
then
    echo "The testing went fine"
    EXIT_CODE=0
else
    echo "The testing resulted in an error"
    EXIT_CODE=1
fi
echo "Finish testing"
echo "Hello!!!!"
cd ..
echo "Well, hello...."

cp ./rspec-tools/link_probes.history "$CACHE_PATH/"

echo "Exiting with $EXIT_CODE"
exit $EXIT_CODE
