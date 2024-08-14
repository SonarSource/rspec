#! /bin/bash

set -euo pipefail

ACTION=${1}
CACHE_NAME=${2}
PATH_TO_CACHE=${3}

CACHE_URL="http://${CIRRUS_HTTP_CACHE_HOST}/${CACHE_NAME}"

TMP_PATH="/tmp/tmp-cache.tgz"

case "${ACTION}" in

download)
  echo "Download cache with key ${CACHE_NAME} from ${CACHE_URL}"
  curl --silent --show-error --fail --location --output "${TMP_PATH}" "${CACHE_URL}" || {
    echo "Cache download failed" >&2
    exit 0
  }
  du -hs "${TMP_PATH}"
  tar -Pxzf "${TMP_PATH}"
  rm "${TMP_PATH}"
  ;;

upload)
  echo "Upload cache to ${CACHE_URL}"
  tar -Pczf "${TMP_PATH}" "${PATH_TO_CACHE}"
  du -hs "${TMP_PATH}"
  curl --silent --show-error -X POST --data-binary "@${TMP_PATH}" "${CACHE_URL}" || {
    echo "Cache upload failed" >&2
    exit 0
  }
  ;;

*)
  echo "Unexpected cache ACTION: ${ACTION}" >&2
  exit 1
  ;;

esac

echo "Cache ${ACTION}ed succeeded."
