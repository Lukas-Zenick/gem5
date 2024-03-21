"""
Restores a full-system simulation from a given checkpoint

To be used in combination with restore_checkpoint_manager.py
"""
import os
import sys
from pathlib import Path

from gem5.resources.resource import obtain_resource, DiskImageResource

from workloads.custom_workloads import CustomFSWorkload
import util.simarglib as simarglib

parser = simarglib.add_parser("Restore Checkpoint FS Workload")
parser.add_argument("--disk_image", required=True, type=str, help="The disk image to use [REQUIRED]")
parser.add_argument("--image_dir", type=str, 
                    default="/scratch/cluster/speedway/gem5_resources/disk_images", 
                    help="The directory in which to look for disk images (default: /scratch/cluster/speedway/gem5_resources/disk_images/)")

class RestoreCheckpointFS(CustomFSWorkload):
    def __init__(self) -> None:
        imageName = simarglib.get("disk_image")
        imageDir = simarglib.get("image_dir")

        start_from = simarglib.get("start_from")
        if start_from:
            chkptDir = Path(start_from)
            if not chkptDir.exists():
                print(f"Checkpoint dir {start_from} does not exist!")
                sys.exit(1)
            print(f"###Restoring from checkpoint: {chkptDir}")
        else:
            print("--start_from is required for RestoreCheckpointFS Workload!")
            sys.exit(1)

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
                f"{imageDir}/{imageName}-image/{imageName}",
                root_partition="1"
            ),
            checkpoint = chkptDir
        )
