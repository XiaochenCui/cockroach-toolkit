#!/usr/bin/env bash

set -o xtrace
set -o errexit
set -o nounset
set -o pipefail

# example usage:
# ./xiaochen-scripts/run-sql.sh add_column

# the first argument is the path to the sql file
SQL_FILE_SYMBOL=$1
SQL_FILE="./xiaochen-scripts/sql/$SQL_FILE_SYMBOL.sql"

DATA_DIR="/home/xiaochen/data/cockroachdb-data"

# remove the old data
rm -rf $DATA_DIR

# start a server in the background
nohup ./cockroach start-single-node --insecure --listen-addr=:26257 --sql-addr=:25258 --store=$DATA_DIR &

SERVER_PID=$!

# wait for the server to start
sleep 5

# run a sql file on the server, then exit
./cockroach sql \
    --url "postgresql://root@localhost:25258/defaultdb?sslmode=disable" \
    --file $SQL_FILE \
    > out

# wait for some background goroutines to finish
sleep 5

# stop the server
kill $SERVER_PID
echo "Background process closed."
