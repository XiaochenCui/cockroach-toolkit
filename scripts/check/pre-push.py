#!/usr/bin/env python3

# Usage: pre-push.py
#
# This script runs the following commands and check their results:
# - ./dev gen
# - ./dev lint
# - ./dev test

import os
import re
from typing import Tuple
import subprocess
import time
import logging
import xiaochen_py

COCKROACH_SRC_DIR = os.path.expanduser("~/code/cockroach")


def run():
    goto_src_dir()
    format_code()
    gen()
    lint()
    test()


def goto_src_dir():
    os.chdir(COCKROACH_SRC_DIR)


def format_code():
    """
    Format the Go code in the changed files.
    """
    # get the list of files that have been changed
    changed_files_output, exit_code = run_command(
        "git diff --name-only upstream/master"
    )
    xiaochen_py.run_command("git diff --name-only upstream/master")
    if exit_code != 0:
        raise Exception("failed to get the list of changed files")

    changed_files = changed_files_output.decode("utf-8").strip().split("\n")

    # filter out the files that are not go files
    changed_go_files = [file for file in changed_files if file.endswith(".go")]

    if not changed_go_files:
        logging.info("no go files changed")
        return

    # run gofmt
    run_command(f"gofmt -s -w {' '.join(changed_go_files)}")

    # install crlfmt
    run_command("go install github.com/cockroachdb/crlfmt")

    # run crlfmt on each Go file
    for file in changed_go_files:
        run_command(f"crlfmt -w {file}")


def gen():
    """
    Run `./dev gen` and check the result.
    """
    output, exit_code = run_command("./dev gen", log_path="gen.log")


def lint():
    """
    Run `./dev lint` and check the result.
    """
    output, exit_code = run_command("./dev lint", log_path="lint.log")


def test():
    """
    Run `./dev test` and check the result.
    """
    log_path = "test.log"

    output, exit_code = run_command("./dev test", log_path=log_path)

    keywords = [
        "ERROR",
        "FAILED TO BUILD",
    ]
    analyaze_test_log(log_path, keywords)


def analyaze_test_log(log_file: str, keywords: list[str]):
    print(f"=== log file <{log_file}> start ===")
    with open(log_file, "r") as file:
        lines = file.readlines()

        for keyword in keywords:
            print(f"=== {keyword} ===")
            # Filter lines that contain any of the keywords
            error_lines = [line for line in lines if keyword in line]
            if error_lines:
                print("".join(error_lines))

        # get the number of lines that contain "NO STATUS"
        print("=== NO STATUS ===")
        no_status_lines = [line for line in lines if "NO STATUS" in line]
        print("number of <NO STATUS> tests:", len(no_status_lines))

        test_results = []
        for line in lines:
            match = re.search(
                r"(?P<test_name>\S+).+PASSED in (?P<duration>\d+\.\ds)", line
            )
            if match:
                test_name = match.group("test_name")
                duration = float(match.group("duration").replace("s", ""))
                test_results.append((test_name, duration))

        # Sort the test results by duration in descending order
        sorted_results = sorted(test_results, key=lambda x: x[1], reverse=True)

        # Print the top 5 tests with the longest durations
        print("Top 5 tests with the longest duration:")
        for test_name, duration in sorted_results[:5]:
            print(f"{duration}s : {test_name}")

    print(f"=== log file <{log_file}> end ===")


if __name__ == "__main__":
    run()
