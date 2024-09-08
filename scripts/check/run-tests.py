#!/usr/bin/env python3

# Usage: run-tests.py <test_directory>
# Example: run-tests.py pkg/ccl/changefeedccl
#
# This script runs all the test files in the specified directory and saves the logs.

import os
import subprocess
import sys

def run_tests_in_dir(test_dir, log_dir):
    # Create the log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Get a list of all test files in the directory
    test_files = [f for f in os.listdir(test_dir) if f.startswith("test") and os.path.isfile(os.path.join(test_dir, f))]

    for test_file in test_files:
        test_path = os.path.join(test_dir, test_file)
        log_file_name = f"{os.path.splitext(test_file)[0]}.log"
        log_path = os.path.join(log_dir, log_file_name)

        # Print the test name, file path, and log path
        print(f"Running test: {test_file}")
        print(f"Test file path: {test_path}")
        print(f"Log path: {log_path}")

        # Run the test and redirect output to the log file
        with open(log_path, "w") as log_file:
            process = subprocess.run(
                ["python3", test_path], stdout=log_file, stderr=subprocess.STDOUT
            )

        # Check the result and stop if there is an error
        if process.returncode != 0:
            print(f"Test {test_file} failed. See log at: {log_path}")
            break
        else:
            print(f"Test {test_file} passed.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <test_directory>")
        sys.exit(1)

    test_directory = sys.argv[1]
    log_directory = "/tmp/logs"
    run_tests_in_dir(test_directory, log_directory)
