#!/usr/bin/env python3

# Run a list of commands provided in a .txt file locally in parallel.
# They will not print to the terminal, so you'll have to redirect the
# stdout/stderr output yourself, either by adding the "--re" flag
# after the "--outdir" flag (for gem5) or adding a shell redirect (">", 
# for other programs) to your command.
#
# Each line in the file represents one command.
# An example is provided in run_commands_locally_sample.txt.

import argparse
import multiprocessing
import os
from typing import List
import sys
import subprocess

def run_command(cmd: str):
    """Run a single command.
    """
    print(f"Running command: \"{cmd.rstrip()}\"")
    # Run command silently (except for errors)
    res = subprocess.run(
        cmd, shell=True, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.PIPE
    ).returncode

    # Check for error
    if res != 0:
        print(f"Command failed: \"{cmd.rstrip()}\" (error code {res}).")
    else:
        print(f"Command completed successfully: \"{cmd.rstrip()}\"")


def run_commands_parallel(cmds: List[str], num_workers: int = 8):
    """Run a series of commands in parallel.
    """
    # Run the commands with a multiprocessing pool
    with multiprocessing.Pool(num_workers) as pool:
        pool.map(run_command, cmds)


def read_command_file(file: str) -> List[str]:
    """Read the commands from a command .txt file.
    """
    # Read the file
    if not os.path.exists(file):
        print(f"File {file} does not exist.")
        return []
    
    cmds = []
    with open(file, "r") as f:
        cmds = f.readlines()

    return cmds

    

if __name__ == "__main__":
    argparse = argparse.ArgumentParser(
        description="Run a list of commands provided in a .txt file on this "
                    "machine in parallel."
    )
    argparse.add_argument(
        "file", type=str, help="Path to the file containing the commands."
    )
    argparse.add_argument(
        "--max-parallel", type=int, default=8, 
        help="Maximum number of commands to run in parallel. Make sure that "
             "you're leaving cores for other people :)"
    )
    args = argparse.parse_args()

    cmds = read_command_file(args.file)
    run_commands_parallel(cmds, args.max_parallel)