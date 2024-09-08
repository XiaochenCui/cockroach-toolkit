#!/usr/bin/env python3

# Usage: check-pr.py <pr_number>
# Example: check-pr.py 127584
#
# This script pull a PR from cockroachdb/cockroach and run the following checks:
# - ./dev gen
# - ./dev lint
# - ./dev test

import os
import re
import sys
import subprocess
import shutil
import time
import requests

REPO_URL = "https://github.com/cockroachdb/cockroach.git"
# use HDD to prevent SSD wear
WORK_DIR_BASE = "/media/xiaochen/large/ci/cockroach/pr-"
BAZEL_CONFIG = os.path.expanduser("~/code/cockroach/.bazelrc.user")


# Skip the actual command execution, only analyze the logs
DRY_RUN = True


def run_command(command, log_file):
    if DRY_RUN:
        print(f"DRY_RUN: {command}")
        return 0

    start_time = time.time()
    print(f"Running command: {command}, log file: {log_file}")
    with open(log_file, "w") as file:
        process = subprocess.Popen(
            command, shell=True, stdout=file, stderr=subprocess.STDOUT
        )
        process.communicate()
    duration = time.time() - start_time
    print(f"Command finished in {duration:.2f} seconds.")
    return process.returncode


def get_pr_title(pr_number):
    url = f"https://api.github.com/repos/cockroachdb/cockroach/pulls/{pr_number}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("title", "Unknown PR")
    else:
        print(f"Failed to fetch PR title: {response.status_code}")
        sys.exit(1)


def main(pr_number):
    # Step 1: Show the title of the PR
    pr_title = get_pr_title(pr_number)
    print(f"PR #{pr_number}: {pr_title}")

    # Step 2: Clone the repo at the PR to a temp directory
    work_dir = f"{WORK_DIR_BASE}{pr_number}"
    code_dir = f"{work_dir}/code"
    log_dir = f"{work_dir}/log"

    if not DRY_RUN:
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        os.makedirs(work_dir)

        os.makedirs(f"{code_dir}")

        os.makedirs(f"{log_dir}")

    # clone the pr directly will cause the error:
    # fatal: Remote branch pull/127584/head not found in upstream origin
    #
    # clone_command = f"git clone --depth 1 --branch pull/{pr_number}/head {REPO_URL} {code_dir}"

    clone_command = f"git clone --depth 1 --branch master {REPO_URL} {code_dir}"
    if run_command(clone_command, f"{log_dir}/clone.log") != 0:
        print(f"Error: Failed to clone the repository.")
        sys.exit(1)

    os.chdir(code_dir)

    fetch_command = f"git fetch origin pull/{pr_number}/head:pr-{pr_number}"
    checkout_command = f"git checkout pr-{pr_number}"

    if (
        run_command(fetch_command, f"{log_dir}/fetch.log") != 0
        or run_command(checkout_command, f"{log_dir}/checkout.log") != 0
    ):
        print(
            f"Error: Failed to checkout PR #{pr_number}, see here for details: {log_dir}/fetch.log and {log_dir}/checkout.log"
        )
        sys.exit(1)

    # Step 3: Copy Bazel config to the work dir
    # The modification to "dev" package must happen before using the "./dev" command.
    bazel_config_dest = os.path.join(code_dir, os.path.basename(BAZEL_CONFIG))
    shutil.copy(BAZEL_CONFIG, bazel_config_dest)

    # Step 4: Inject code
    # code_inject(code_dir, log_dir)

    # Step 5: Run the required commands
    commands = {
        "doctor": "./dev doctor",
        "gen": "./dev gen",
        "lint": "./dev lint",
        # "test": "./dev test",
        "test": " ./dev test --timeout 10m -- --experimental_remote_cache_eviction_retries 3",
    }

    logs = {}
    for step, command in commands.items():
        log_file = f"{log_dir}/{step}.log"
        logs[step] = log_file
        if run_command(command, log_file) != 0:
            print(f"Error: {step} failed, see {log_file} for details.")
            break
    else:
        print("All steps completed successfully.")

    # Step 6: Summarize the output
    for step, log_file in logs.items():
        match step:
            case "test":
                keywords = [
                    "ERROR",
                    "FAILED TO BUILD",
                ]
                analyaze_test_log(log_file, keywords)
            case _:
                continue


def code_inject(code_dir: str, log_dir: str):
    target = (
        """err := d.exec.CommandContextInheritingStdStreams(ctx, "bazel", args...)"""
    )
    insert = """args = append(args, "--experimental_remote_cache_eviction_retries=3")"""
    file_path = os.path.join(code_dir, "pkg/cmd/dev/test.go")
    insert_string_before_line(file_path, target, insert)

    command = "gofmt -s -w pkg/cmd/dev/test.go"
    log_file = f"{log_dir}/gofmt.log"
    if run_command(command, log_file) != 0:
        print(f"Error: gofmt failed, see {log_file} for details.")
        sys.exit(1)


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

        # lines = file.readlines()
        # for line in lines:
        #     re.match(r'^
        #     match = re.search(r'PASSED in (\d+\.\ds)', line)
        #     if match:
        #         duration = float(match.group(1).replace('s', ''))
        #         test_name = line.split('PASSED')[0].strip()
        #         test_results.append((test_name, duration))
        #     lines = file.readlines()
        for line in lines:
            match = re.search(r'(?P<test_name>\S+).+PASSED in (?P<duration>\d+\.\ds)', line)
            if match:
                test_name = match.group("test_name")
                duration = float(match.group("duration").replace('s', ''))
                test_results.append((test_name, duration))

        # Sort the test results by duration in descending order
        sorted_results = sorted(test_results, key=lambda x: x[1], reverse=True)

        # Print the top 5 tests with the longest durations
        print("Top 5 tests with the longest duration:")
        for test_name, duration in sorted_results[:5]:
            print(f"{duration}s : {test_name}")

    print(f"=== log file <{log_file}> end ===")


def insert_string_before_line(file_path, target_line_content, string_to_insert):
    """
    Inserts a string at the beginning of a line with the exact content match in a file.

    Args:
        file_path (str): The path to the file.
        target_line_content (str): The exact content of the line where the string should be inserted before.
        string_to_insert (str): The string to insert at the beginning of the specified line.
    """
    # Read the existing file content
    with open(file_path, "r") as file:
        lines = file.readlines()

    # Find and modify the target line
    modified = False
    for i, line in enumerate(lines):
        if line.strip() == target_line_content:
            lines[i] = string_to_insert + "\n" + line
            modified = True
            break

    if not modified:
        print(f"Error: Line with content '{target_line_content}' not found.")
        return

    # Write the modified content back to the file
    with open(file_path, "w") as file:
        file.writelines(lines)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: check-pr.py <pr_number>")
        sys.exit(1)

    pr_number = sys.argv[1]
    main(pr_number)
