"""
Hello world in syscall emulation
"""
import os
import sys

from gem5.resources.resource import BinaryResource

from workloads.custom_workloads import CustomSEWorkload
import util.simarglib as simarglib

class HelloWorldSE(CustomSEWorkload):
    def __init__(self) -> None:
        start_from = simarglib.get("start_from")
        if start_from:
            print("--start_from not supported by HelloWorldSE Workload")
            sys.exit(1)

        gem5_path = os.getenv('GEM5_HOME')
        if not gem5_path:
            print('$GEM5_HOME not defined in your environment')
            sys.exit(1)
        path = os.path.join(gem5_path, 'tests/test-progs/hello/bin/x86/linux/hello')

        super().__init__(
            binary = BinaryResource(path)
        )
