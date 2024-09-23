#!/usr/bin/env python3

# Identify which unit test calls a specific piece of code.
#
# Usage: identify-test.py <path-to-code>
# Example: identify-test.py cockroach/pkg/kv/kvserver/queue.go:1204


import os
import re
import subprocess
import sys
import threading
import time
from typing import Tuple


COCKROACH_ROOT = os.path.expanduser("~/code/cockroach")


def identify_test(code_file: str, code_line: int) -> list[str]:
    """
    Identify which unit test calls a specific line of code.

    Return a list of tests that call the code.
    The tests are of the form "pkg/subpkg:TestName".

    Example:
    >>> identify_test("cockroach/pkg/kv/kvserver/queue.go", 1204)
    ["pkg/kv/kvserver:TestQueue"]
    """
    print(f"Identifying tests for {code_file}:{code_line}...")

    # cd to the root of the cockroach repo
    os.chdir(COCKROACH_ROOT)

    # truncate the "cockroach/" prefix from the code file
    code_file = code_file.replace("cockroach/", "")

    # remove the file name to get the package path
    package_path = os.path.dirname(code_file)

    # inject panic into the code to identify the test
    inject_code(
        code_file,
        code_line,
        """
        panic("IDENTIFY_TEST")
        """,
    )

    output = run_command(
        f"./dev test {package_path}",
        output_file="/tmp/out",
        # stream_output=True,
        stream_output=False,
        kill_on_output="panic",
    )

    # analyze the output to identify the test
    # test example:
    # github.com/cockroachdb/cockroach/pkg/kv/kvserver_test.TestStoreRangeUpReplicate(0xc00872c000)
    # =>
    # pkg/kv/kvserver:TestStoreRangeUpReplicate
    test_pattern = re.compile(
        r"github\.com/cockroachdb/cockroach/(pkg/.+)\.(Test[A-Za-z0-9_]+)\("
    )

    tests = []
    for match in test_pattern.finditer(output):
        package_path = match.group(1)
        test_name = match.group(2)
        if test_name == "TestMain":
            continue

        formatted_test = f"{package_path}:{test_name}"
        tests.append(formatted_test)

    # print the count of lines in the output
    print(f"Output lines: {len(output.splitlines())}")

    for test in tests:
        print(test)


def inject_code(code_file: str, code_line: int, injected_code: str):
    """
    Inject code into a specific line of a file.

    Throws an exception if any error occurs.
    """
    with open(code_file, "r") as f:
        lines = f.readlines()

    # Return if the injected code is already present
    output = "".join(lines)
    if injected_code in output:
        return

    lines.insert(code_line - 1, injected_code)

    with open(code_file, "w") as f:
        f.write("".join(lines))


from typing import Tuple, Optional


def run_command(
    command: str,
    include_stderr: bool = True,
    output_file: Optional[str] = None,
    stream_output: bool = False,
    kill_on_output: Optional[str] = None,
) -> Tuple[str, int]:
    """
    Run a shell command and return its output and exit code.

    Args:
        command (str): The shell command to execute.
        include_stderr (bool, optional): If True, stderr is included in the output. Defaults to True.
        output_file (Optional[str], optional): The file path where output will be written in real-time. If None, no file is written.
                                               If the file exists, it will be overwritten. Defaults to None.
        stream_output (bool, optional): If True, streams the output to stdout while executing. Defaults to False.
        kill_on_output (Optional[str], optional): If the given string is found in the output, the process will be killed after 1 second.
                                                 Defaults to None.

    Returns:
        Tuple[str, int]: A tuple containing the output of the command as a string and the exit code of the process.
    """
    f = None
    if output_file:
        f = open(output_file, "w")

    print(f"Running command: {command}")
    print(f"Running command: {command}", file=f)

    # Set up the subprocess command
    stderr_option = subprocess.STDOUT if include_stderr else None
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=stderr_option, text=True
    )

    output = []
    kill_event = threading.Event()

    def monitor_output():
        while process.poll() is None:
            # process is still running

            line = process.stdout.readline()
            if not line:
                break
            if stream_output:
                print(line, end="")  # Stream the output to stdout
            output.append(line)
            if f:
                f.write(line)  # Write output to the file in real-time
                f.flush()  # Ensure the output is written immediately
            if kill_on_output:
                if kill_on_output in line:
                    kill_event.set()

    def control_process():
        kill_event.wait()

        # sleep for 1 second for more output
        time.sleep(1)

        process.kill()

    # Start monitoring the output in a separate thread
    thread = threading.Thread(target=monitor_output)
    thread.start()

    # Start the control process in a separate thread
    control_thread = threading.Thread(target=control_process)
    control_thread.start()

    thread.join()  # Wait for the thread to finish
    control_thread.join()  # Wait for the control thread to finish

    process.wait()  # Ensure the process has terminated
    return "".join(output)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: identify-test.py <path-to-code>")
        sys.exit(1)

    code_path = sys.argv[1]
    code_path = code_path.split(":")
    if len(code_path) != 2:
        print("Invalid path")
        sys.exit(1)

    code_file = code_path[0]
    code_line = int(code_path[1])
    identify_test(code_file, code_line)
