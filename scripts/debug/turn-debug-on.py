#!/usr/bin/env python3

import os
from pathlib import Path
import shutil


COCKROACH_SRC_PATH = os.path.expanduser("~/code/cockroach/")


def patch_all_files():
    directory = "./scaffold-code"

    for entry in os.listdir(directory):
        path = os.path.join(directory, entry)
        if os.path.isfile(path):
            patch_file(path)


def patch_file(file_path):
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
    shutil.copy(file_path, target_location)
    print(f"File copied to {target_location}")


if __name__ == "__main__":
    patch_all_files()
