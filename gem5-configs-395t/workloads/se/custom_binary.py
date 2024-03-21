"""
Syscall emulation workload to run an arbitrary input binary and its arguments
"""
import os
import sys

from gem5.resources.resource import BinaryResource

from workloads.custom_workloads import CustomSEWorkload
import util.simarglib as simarglib

parser = simarglib.add_parser("Custom Binary SE Workload")
parser.add_argument("--input_bin", required=True, type=str, help="The input binary to simulate [REQUIRED]")
parser.add_argument("--input_args", type=str, help="The arguments to provide the binary to simulate (NOTE: multiple arguments must be wrapped in quotes!)")

class CustomBinarySE(CustomSEWorkload):
    def __init__(self) -> None:
        inbin = simarglib.get("input_bin")
        inargs = simarglib.get("input_args")

        start_from = simarglib.get("start_from")
        if start_from:
            print("--start_from not supported by CustomBinarySE Workload")
            sys.exit(1)

        if not os.path.isabs(inbin):
            inbin = os.path.join(os.getcwd(), inbin)
        if not os.path.exists(inbin):
            print(f"Input binary {inbin} does not exist!")
            sys.exit(1)

        super().__init__(
            binary = BinaryResource(inbin),
            arguments = inargs.split() if inargs else []
        )
