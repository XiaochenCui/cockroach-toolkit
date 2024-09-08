#!/usr/bin/env python3

# Usage: analyze-log.py <log_file>
# Example: analyze-log.py out
#
# This script analyzes the log file generated by "./dev lint" or "./dev test".

# TODO


def analyze_log(log_file):
    with open(log_file, "r") as file:
        lines = file.readlines()

    # analyze lint errors


    # Count the number of errors
    error_count = 0
    for line in lines:
        if "error" in line.lower():
            error_count += 1

    # Count the number of warnings
    warning_count = 0
    for line in lines:
        if "warning" in line.lower():
            warning_count += 1

    print(f"Errors: {error_count}")
    print(f"Warnings: {warning_count}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <log_file>")
        sys.exit(1)

    log_file = sys.argv[1]