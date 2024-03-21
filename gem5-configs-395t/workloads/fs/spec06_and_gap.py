"""
Full-system SPEC 2006 and GAP single-threaded benchmarks
"""
import os
import sys
from pathlib import Path

from gem5.resources.resource import obtain_resource, DiskImageResource

from workloads.custom_workloads import CustomFSWorkload
import util.simarglib as simarglib

parser = simarglib.add_parser("SPEC 2006 and (Single-Threaded) GAP FS Workload")
parser.add_argument("--benchmark", required=True, type=str, choices=["astar", "bwaves",
    "bzip", "cactusADM", "calculix", "gcc", "GemsFDTD", "h264ref", "hmmer", "lbm", 
    "leslie", "libquantum", "mcf", "milc", "omnetpp", "soplex", "sphinx3", "tonto", 
    "xalancbmk", "zeusmp", "bfs", "cc", "pr", "sssp"], 
    help="The benchmark to simulate [REQUIRED]")

class Spec06AndGapFS(CustomFSWorkload):
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
            'astar':      'cd spec06/473.astar      ; ./473.astar BigLakes2048.cfg',
            'bwaves':     'cd spec06/410.bwaves     ; ./410.bwaves',
            'bzip':       'cd spec06/401.bzip2      ; ./401.bzip2 liberty.jpg 30',
            'cactusADM':  'cd spec06/436.cactusADM  ; ./436.cactusADM benchADM.par',
            'calculix':   'cd spec06/454.calculix   ; ./454.calculix -i hyperviscoplastic',
            'gcc':        'cd spec06/403.gcc        ; ./403.gcc 166.i -o 166.s',
            'GemsFDTD':   'cd spec06/459.GemsFDTD   ; ./459.GemsFDTD',
            'h264ref':    'cd spec06/464.h264ref    ; ./464.h264ref -d foreman_ref_encoder_baseline.cfg',
            'hmmer':      'cd spec06/456.hmmer      ; ./456.hmmer nph3.hmm swiss41',
            'lbm':        'cd spec06/470.lbm        ; ./470.lbm 3000 reference.dat 0 0 100_100_130_ldc.of',
            'leslie':     'cd spec06/437.leslie3d   ; ./437.leslie3d < leslie3d.in',
            'libquantum': 'cd spec06/462.libquantum ; ./462.libquantum 1397 8',
            'mcf':        'cd spec06/429.mcf        ; ./429.mcf inp.in',
            'milc':       'cd spec06/433.milc       ; ./433.milc < su3imp.in',
            'omnetpp':    'cd spec06/471.omnetpp    ; ./471.omnetpp omnetpp.ini',
            'soplex':     'cd spec06/450.soplex     ; ./450.soplex -s1 -e -m45000 pds-50.mps',
            'sphinx3':    'cd spec06/482.sphinx3    ; ./482.sphinx3 ctlfile . args.an4',
            'tonto':      'cd spec06/465.tonto      ; ./465.tonto',
            'xalancbmk':  'cd spec06/483.xalancbmk  ; ./483.xalancbmk -v t5.xml xalanc.xsl > /dev/null',
            'zeusmp':     'cd spec06/434.zeusmp     ; ./434.zeusmp',
            'bfs':        'cd gap                   ; ./bfs -r 1 -f ./graphs/g22.el',
            'cc':         'cd gap                   ; ./cc -r 1 -f ./graphs/g22.el',
            'pr':         'cd gap                   ; ./pr -r 1 -f ./graphs/g22.el',
            'sssp':       'cd gap                   ; ./sssp -r 1 -f ./graphs/g22.el',
            'tc':         'cd gap                   ; ./tc -r 1 -f ./graphs/g22.el'
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
                "/scratch/cluster/speedway/gem5_resources/disk_images/spec06-and-gap-image/spec06-and-gap",
                root_partition="1"
            ),
            readfile_contents = command,
            checkpoint = chkptDir
        )
