#!/usr/bin/env bash

set -o xtrace
# we have to continue even if some commands fail
# set -o errexit
set -o nounset
# we have to continue even if some commands fail
# set -o pipefail

COCKROACH_SRC_DIR=$HOME/code/cockraoch
TOOLKIT_DIR=$HOME/code/cockroach-toolkit

cd $COCKROACH_SRC_DIR

# remove scaffold files
# $TOOLKIT_DIR/scripts/debug/turn-debug.py off

# ========================================
# check the code style
# ========================================

# get the list of files that have been changed
CHANGED_FILES=$(git diff --name-only upstream/master)

# filter out the files that are not go files
CHANGED_FILES=$(echo $CHANGED_FILES | tr " " "\n" | grep "\.go$")

gofmt -s -w $CHANGED_FILES

go install github.com/cockroachdb/crlfmt

# "crlfmt" doesn't support multiple paths
for file in $CHANGED_FILES; do
  crlfmt -w $file
done

# ========================================
# run the tests
# ========================================

# clear the output file
echo "" > out

echo "running ./dev cache --reset" >> out
./dev cache --reset 2>&1 | tee -a out

echo "running ./dev gen" >> out
./dev gen 2>&1 | tee -a out

echo "running ./dev lint" >> out
./dev lint 2>&1 | tee -a out

echo "running ./dev test" >> out
# this may has error "ERROR: Build did NOT complete successfully"
./dev test 2>&1 | tee -a out
# this may has error "ERROR: Build did NOT complete successfully"
# ./dev test --ignore-cache 2>&1 | tee -a out
# this may has error "ERROR: exit status 7"
# ./dev test --changed 2>&1 | tee -a out

# print "ERROR" messages
grep -A 3 "ERROR" out

# print "FAILED" messages
grep -A 3 "FAILED" out

# print "FAIL:" messages
grep -A 3 "FAIL:" out
