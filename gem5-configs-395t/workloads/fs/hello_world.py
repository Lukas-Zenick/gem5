"""
Full-system hello world
"""
import os
import sys
from pathlib import Path

from gem5.resources.resource import obtain_resource, DiskImageResource

from workloads.custom_workloads import CustomFSWorkload
import util.simarglib as simarglib

class HelloWorldFS(CustomFSWorkload):
    def __init__(self) -> None:
        start_from = simarglib.get("start_from")
        if start_from:
            chkptDir = Path(start_from)
            if not chkptDir.exists():
                print(f"Checkpoint dir {start_from} does not exist!")
                sys.exit(1)
            print(f"###Restoring from checkpoint: {chkptDir}")
        else:
            chkptDir = None

        command = (
            "m5 workbegin;"
            + "echo 'Hello world!';"
            + "m5 workend;"
            + "sleep 1;" # don't cut off output
            + "m5 exit;"
        )
# Note: if you leave the above command string blank on this disk image,
# the simulation will drop to a shell prompt and you can run any command
# you want, including executing benchmarks wrapped in workbegin/workend,
# e.g.:
#    m5 workbegin; ./matmull_small; m5 workend;
# To interact with the simulated shell prompt, build m5term and connect:
#    > cd gem5/util/term; make
#    > ./gem5/util/term/m5term localhost 3456

        # Resource images will be downloaded to $GEM5_RESOURCES_DIR
        resource_path = os.getenv('GEM5_RESOURCE_DIR')
        if not resource_path:
            print("$GEM5_RESOURCE_DIR is not defined in your environment!"
                  "Careful: this will put very large files in ~/.cache/")

        super().__init__(
            kernel = obtain_resource("x86-linux-kernel-4.19.83"),
            # The second arg here tells gem5 where the root partition is
            # (the string given will be appended to '/dev/hda')
            disk_image = DiskImageResource(
                "/scratch/cluster/speedway/gem5_resources/disk_images/ubuntu-18.04-image/ubuntu-18.04",
                root_partition="1"
            ),
            readfile_contents = command,
            checkpoint = chkptDir
        )
