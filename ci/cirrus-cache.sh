#! /bin/bash

set -euo pipefail

ACTION=${1}
CACHE_NAME=${2}
PATH_TO_CACHE=${3}

CACHE_KEY=${CACHE_NAME}
DEFAULT_CACHE_KEY=${CACHE_NAME}

CACHE_URL=http://${CIRRUS_HTTP_CACHE_HOST}/${CACHE_KEY}

TMP_PATH=/tmp/tmp-cache.tgz

case "${ACTION}" in

download)
  echo "Download cache with key ${CACHE_KEY}"

  echo "  -> try ${CACHE_URL}"
  curl -sfSL -o ${TMP_PATH} ${CACHE_URL} || {
    echo "Cache download failed";
    exit 0;
  }
  du -hs ${TMP_PATH}
  tar -Pxzf ${TMP_PATH}
  rm ${TMP_PATH}
  ;;

upload)
  echo "Upload cache to ${CACHE_URL}"
  tar -Pczf ${TMP_PATH} ${PATH_TO_CACHE}
  du -hs ${TMP_PATH}
  curl -s -X POST --data-binary @${TMP_PATH} ${CACHE_URL}
  ;;

*)
  echo "Unexpected cache ACTION: ${ACTION}"
  exit 1
  ;;

esac
