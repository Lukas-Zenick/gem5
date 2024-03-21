"""
Full-system GAP and Parsec multi-threaded benchmarks

Must be used in combination with a --cores N arg
"""
import os
import sys
from pathlib import Path

from gem5.resources.resource import obtain_resource, DiskImageResource

from workloads.custom_workloads import CustomFSWorkload
import util.simarglib as simarglib

parser = simarglib.add_parser("GAP and Parsec Multi-Threaded FS Workload")
parser.add_argument("--benchmark", required=True, type=str, choices=[
                        # GAP
                        "bc", "bfs", "cc", "pr", "sssp", "tc",
                        # Parsec
                        "blackscholes", "bodytrack", "canneal", "dedup", "facesim",
                        "ferret", "fluidanimate", "freqmine", "raytrace",
                        "streamcluster", "swaptions", "vips", "x264"
                    ], help="The benchmark to simulate [REQUIRED]")
parser.add_argument("--size", required=True, type=str,
                    choices=["small", "medium", "large"], help="Input size [REQUIRED]")

# Full list of inputs available on this disk image:
#   graphs/roads:
#     USA-road-d.BAY.gr  USA-road-d.CTR.gr  USA-road-d.LKS.gr  USA-road-d.NY.gr
#     USA-road-d.CAL.gr  USA-road-d.E.gr    USA-road-d.NE.gr   USA-road-d.USA.gr
#     USA-road-d.COL.gr  USA-road-d.FLA.gr  USA-road-d.NW.gr   USA-road-d.W.gr
#   graphs/synth:
#     g100k.sg  g100k.wsg  g16m.sg  g1m.sg  g1m.wsg  g2m.sg  g2m.wsg  
#     g4m.sg  g4m.wsg  g500k.sg  g8m.sg
#
# The benchmarks are from the DArchR versions of each benchmark suite, with
# m5 workbegin/workend delimiting the ROI of each

class GapAndParsecFS(CustomFSWorkload):
    def __init__(self) -> None:
        benchmark = simarglib.get("benchmark")
        size = simarglib.get("size")

        start_from = simarglib.get("start_from")
        if start_from:
            chkptDir = Path(start_from)
            if not chkptDir.exists():
                print(f"Checkpoint dir {start_from} does not exist!")
                sys.exit(1)
            print(f"###Restoring from checkpoint: {chkptDir}")
        else:
            chkptDir = None

        # --cores simarg defined in CustomX86(Switchable)Processor
        # (with default value of 1)
        cores = simarglib.get("cores")
        if not cores:
            print("Number of cores is undefined! Must import Processor module with --cores simarg!")
            sys.exit(1)

        if benchmark in ["bc", "bfs", "cc", "pr"]:
            if size == "small":
                inputName = "USA-road-d.COL.gr"
            elif size == "medium":
                inputName = "USA-road-d.CAL.gr"
            else:
                inputName = "USA-road-d.CTR.gr"
            command = (
                "cd /home/gem5/gapbs;"
                f"./{benchmark} -n 1 -r 1 -f ../graphs/roads/{inputName};"
            )
        elif benchmark in ["sssp"]:
            if size == "small":
                inputName = "g100k.wsg"
            elif size == "medium":
                inputName = "g1m.wsg"
            else:
                inputName = "g4m.wsg"
            command = (
                "cd /home/gem5/gapbs;"
                f"./{benchmark} -n 1 -r 1 -f ../graphs/synth/{inputName};"
            )
        elif benchmark in ["tc"]:
            if size == "small":
                inputName = "g100k.sg"
            elif size == "medium":
                inputName = "g500k.sg"
            else:
                inputName = "g1m.sg"
            command = (
                "cd /home/gem5/gapbs;"
                f"./{benchmark} -n 1 -r 1 -f ../graphs/synth/{inputName};"
            )
        else:
            inputName = "sim" + size
            command = (
                "cd /home/gem5/parsec-benchmark;"
                "source env.sh;"
                f"parsecmgmt -a run -p {benchmark} -c gcc-hooks -i {inputName} -n {cores};"
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
                "/scratch/cluster/speedway/gem5_resources/disk_images/gap-and-parsec-image/gap-and-parsec",
                root_partition="1"
            ),
            readfile_contents = command,
            checkpoint = chkptDir
        )
