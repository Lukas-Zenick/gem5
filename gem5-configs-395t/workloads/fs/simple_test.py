"""
Small full-system test benchmarks (bfs and matmul)
"""
import os
import sys
from pathlib import Path

from gem5.resources.resource import obtain_resource, DiskImageResource

from workloads.custom_workloads import CustomFSWorkload
import util.simarglib as simarglib

parser = simarglib.add_parser("Simple Test FS Workload")
parser.add_argument("--benchmark", required=True, type=str, choices=["bfs", "mm"],
                    help="The test program to simulate [REQUIRED]")

class SimpleTestFS(CustomFSWorkload):
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

        commands = {
            'bfs' : './bfs -n 1 -r 1 -f bfs_small.sg',
            'mm' : './matmul_small'
        }

        command = (
            "m5 workbegin;"
            + commands[simarglib.get("benchmark")] + ';'
            + "m5 workend;"
            + "sleep 1;" # don't cut off output
            + "m5 exit;"
        )

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
