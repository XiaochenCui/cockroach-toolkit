#!/usr/bin/env python3

# Usage: check-pr.py <pr_number>
# Example: check-pr.py 127584
#
# This script pull a PR from cockroachdb/cockroach and run the following checks:
# - ./dev gen
# - ./dev build
# - ./dev lint
# - ./dev test

import os
import sys
import subprocess
import shutil
import time
import requests

# Constants
REPO_URL = "https://github.com/cockroachdb/cockroach.git"
WORK_DIR_BASE = "/media/xiaochen/large/ci/cockroach/pr-"
BAZEL_CONFIG = os.path.expanduser("~/code/cockroach/.bazelrc.user")


# Skip the actual command execution, only analyze the logs
DRY_RUN = False


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
    bazel_config_dest = os.path.join(code_dir, os.path.basename(BAZEL_CONFIG))
    shutil.copy(BAZEL_CONFIG, bazel_config_dest)

    # Step 4: Run the required commands
    commands = {
        "doctor": "./dev doctor",
        "gen": "./dev gen",
        # "build": "./dev build",
        "lint": "./dev lint",
        "test": "./dev test --ignore-cache",
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

    # Step 5: Summarize the output
    for step, log_file in logs.items():
        match step:
            case "test":
                print(f"=== summary of {step} start ===")
                with open(log_file, "r") as file:
                    output = file.read()
                    error_lines = [
                        line
                        for line in output
                        if "error" in line.lower() or "failed" in line.lower()
                    ]
                    if error_lines:
                        print("".join(error_lines))
                print(f"=== summary of {step} end ===")
            case _:
                continue

        with open(log_file, "r") as file:
            output = file.read()
            if "error" in output.lower() or "failed" in output.lower():
                print(f"Summary of {step}: Failed - see {log_file} for details.")
            else:
                print(f"Summary of {step}: Success")


def print_log(log_file):
    with open(log_file, "r") as file:
        lines = file.readlines()
        error_lines = [
            line
            for line in lines
            if "error" in line.lower() or "failed" in line.lower()
        ]
        if error_lines:
            print("".join(error_lines))


def print_log(log_file: str, keywords: list[str]):
    with open(log_file, "r") as file:
        lines = file.readlines()

        for keyword in keywords:
            # Filter lines that contain any of the keywords
            error_lines = [line for line in lines if keyword in line]
            if error_lines:
                print("".join(error_lines))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: check-pr.py <pr_number>")
        sys.exit(1)

    pr_number = sys.argv[1]
    main(pr_number)
