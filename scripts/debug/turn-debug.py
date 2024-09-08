#!/usr/bin/env python3

import os
import shutil
import sys

COCKROACH_SRC_PATH = os.path.expanduser("~/code/cockroach")
TOOLKIT_PATH = os.path.expanduser("~/code/cockroach-toolkit")


def patch_all_files(mode: str):
    directory = os.path.join(TOOLKIT_PATH, "scaffold-code")
    for entry in os.listdir(directory):
        path = os.path.join(directory, entry)
        if os.path.isfile(path):
            patch_file(path, mode=mode)


def patch_file(file_path, mode: str):
    # step 1: extract target location
    #
    # Extract the target location from the first line.
    # Assuming the format is "// target location: <path>"
    target_location = None
    with open(file_path, "r") as file:
        # Read the first line
        first_line = file.readline().strip()

    if first_line.startswith("// target location:"):
        target_location = first_line.split(":", 1)[1].strip()
        print(target_location)
    else:
        raise ValueError("Target location not found in the first line")

    # step 2: copy the file to the target location
    target_location = os.path.join(COCKROACH_SRC_PATH, target_location)
    match mode:
        case "on":
            shutil.copy(file_path, target_location)
            print(f"File copied to {target_location}")
        case "off":
            os.remove(target_location)
            print(f"File removed from {target_location}")


if __name__ == "__main__":
    # the first argument is the mode
    if len(sys.argv) != 2:
        print("Usage: turn-debug.py <on|off>")
        sys.exit(1)

    mode = sys.argv[1]
    patch_all_files(mode)