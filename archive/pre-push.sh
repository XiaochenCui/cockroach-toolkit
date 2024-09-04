#!/usr/bin/env bash

set -o xtrace
# we have to continue even if some commands fail
# set -o errexit
set -o nounset
# we have to continue even if some commands fail
# set -o pipefail

# get the list of files that have been changed
CHANGED_FILES=$(git diff --name-only upstream/master)

# filter out the files that are not go files
CHANGED_FILES=$(echo $CHANGED_FILES | tr " " "\n" | grep "\.go$")

gofmt -s -w $CHANGED_FILES

# clear the output file
echo "" > out

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
