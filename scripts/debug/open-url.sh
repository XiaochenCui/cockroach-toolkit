#!/usr/bin/env bash

set -o xtrace
set -o errexit
set -o nounset
set -o pipefail

# This script should be run on the laptop.
# 
# example usage:
# ./scripts/debug/open-url.sh
# fetch file "out" from the remote server, and open all the URLs in the file

REMOTE_SERVER="xc"
REMOTE_FILE="/home/xiaochen/code/cockroach/out"

scp "${REMOTE_SERVER}:${REMOTE_FILE}" /tmp/out

while read -r line; do
    # open it if it starts with "http"
    if [[ $line == http* ]]; then
        open "$line"
    fi
done < /tmp/out