#!/usr/bin/env python3

# Usage: run-tests.py <test_directory>
# Example: run-tests.py pkg/ccl/changefeedccl
#
# This script runs all the test files in the specified directory and saves the logs.


import os
import subprocess
import re
import sys
import time


def extract_test_names(file_path):
    """Extracts all test names from a Go test file."""
    test_names = []
    with open(file_path, "r") as file:
        content = file.read()
        # Regular expression to match Go test function names
        matches = re.findall(r"^func\s+(Test\w+)\s*\(.*\)\s*{", content, re.MULTILINE)
        test_names.extend(matches)
    return test_names


def run_tests_in_dir(test_dir, log_dir):
    """Runs all Go tests in the specified directory."""
    for file in os.listdir(test_dir):
        if file.endswith("_test.go"):
            file_path = os.path.join(test_dir, file)
            test_names = extract_test_names(file_path)

            for test_name in test_names:
                print("-" * 80)
                print(f"Running test: {test_name}")
                print(f"File path: {file_path}")

                log_file_path = os.path.join(log_dir, f"{test_name}.log")
                print(f"Log path: {log_file_path}")

                # Construct the Go test command
                cmd = f"go test -timeout 3m -run ^{test_name}$ github.com/cockroachdb/cockroach/pkg/ccl/changefeedccl -v -count=1"

                start_time = time.time()
                with open(log_file_path, "w") as log_file:
                    result = subprocess.run(
                        cmd, shell=True, stdout=log_file, stderr=subprocess.STDOUT
                    )
                duration = time.time() - start_time
                print(f"Test finished in {duration:.2f} seconds.")

                # Report the result
                if result.returncode != 0:
                    print(f"Test {test_name} failed. See log file: {log_file_path}")
                    return  # Stop if there is an error
                else:
                    print(f"Test {test_name} passed.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <test_directory>")
        sys.exit(1)

    test_directory = sys.argv[1]
    log_directory = "/tmp/logs"
    run_tests_in_dir(test_directory, log_directory)
