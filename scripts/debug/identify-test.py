#!/usr/bin/env python3

# Identify which unit test calls a specific piece of code.
#
# Usage: identify-test.py <path-to-code>
# Example: identify-test.py cockroach/pkg/kv/kvserver/queue.go:1204


import os
import subprocess
import sys
import threading
import time


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

    # print the count of lines in the output
    print(f"Output lines: {len(output.splitlines())}")


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


def run_command(
    command: str,
    include_stderr: bool = True,
    output_file: str = None,
    stream_output: bool = False,
    kill_on_output: str = None,
) -> str:
    """
    Run a shell command and return its output.

    Args:
    - command: The shell command to run.
    - include_stderr: Whether to include stderr in the output.
    - output_file: The file to write the output to in real-time, if it's not None.
                   If the file doesn't exist, it will be created. If it does exist, it will be overwritten.
    - stream_output: Whether to stream the output to stdout.
    - kill_on_output: If this string is found in the output, kill the process after 1 second.

    Returns:
    - The output of the command as a string.
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
