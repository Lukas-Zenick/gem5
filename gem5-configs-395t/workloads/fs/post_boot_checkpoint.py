"""
Creates a re-usable full-system checkpoint at the end of OS boot

To be used in combination with post_boot_checkpoint_manager.py
"""
import os
import sys

from gem5.resources.resource import obtain_resource, DiskImageResource

from workloads.custom_workloads import CustomFSWorkload
import util.simarglib as simarglib

parser = simarglib.add_parser("Post-OS Boot Checkpoint FS Workload")
parser.add_argument("--disk_image", required=True, type=str, help="The disk image to use [REQUIRED]")
parser.add_argument("--image_dir", type=str, 
                    default="/scratch/cluster/speedway/gem5_resources/disk_images", 
                    help="The directory in which to look for disk images (default: /scratch/cluster/speedway/gem5_resources/disk_images/)")

class PostBootCheckpointFS(CustomFSWorkload):
    def __init__(self) -> None:
        imageName = simarglib.get("disk_image")
        imageDir = simarglib.get("image_dir")

        start_from = simarglib.get("start_from")
        if start_from:
            print("--start_from not supported by PostBootCheckpointFS Workload!")
            sys.exit(1)

        # This is a slightly-edited version of gem5/configs/boot/hack_back_ckpt.rcS
        # The first time we invoke our runscript, we call m5 checkpoint. On restore,
        # we use an env variable to detect we should instead load a NEW runscript,
        # which has the actual command to execute.  This allows a post-OS boot 
        # checkpoint to invoke any arbitrary command upon restoration, rather than 
        # being restricted to the benchmark that was invoked when the checkpoint
        # was created.
        hackback = ("""
            # Test if the RUNSCRIPT_VAR environment variable is already set
            if [ "${RUNSCRIPT_VAR+set}" != set ]
            then
                # Signal our future self that it's safe to continue
                export RUNSCRIPT_VAR=1
            else
                # We've already executed once, so we should exit
                /sbin/m5 exit
            fi

            # Checkpoint the first execution
            echo "Checkpointing simulation..."
            m5 checkpoint
             
            # Test if we previously okayed ourselves to run this script
            if [ "$RUNSCRIPT_VAR" -eq 1 ]
            then
                # Signal our future self not to recurse infinitely
                export RUNSCRIPT_VAR=2

                # Read the new command for the checkpoint restored execution
                echo "Loading new run command..."
                m5 readfile > new_commands.sh 
                chmod +x new_commands.sh

                # Execute the new runscript
                if [ -s new_commands.sh ]
                then
                    echo "Executing new run command..."
                    ./new_commands.sh
                else
                    echo "ERROR: new run command not specified!"
                fi
            fi
        """)

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
            readfile_contents = hackback
        )
