#!/usr/bin/env bash

set -o xtrace
set -o errexit
set -o nounset
set -o pipefail

# entry point
TLA_JAR="/home/xiaochen/Downloads/tla2tools.jar"

# subcommands
FINITE_MODEL_CHECKER="tlc2.TLC"

TLA_FILE="/home/xiaochen/code/cockroach/docs/tla-plus/ParallelCommits/ParallelCommits.tla"
CONFIG_FILE="/home/xiaochen/code/cockroach/docs/tla-plus/ParallelCommits/ParallelCommits.cfg"

java -cp ${TLA_JAR} ${FINITE_MODEL_CHECKER} ${TLA_FILE} -config ${CONFIG_FILE}
