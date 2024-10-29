"""
Run a simulation in full-system mode,
beginning execution on the KVM (or atomic) core and, beginning
at benchmark execution, switching between KVM and O3 at a periodic
sampling rate with an ROI stats section for each switch.
"""
import argparse
import os
import sys
import time

import m5
from m5.objects import *

from gem5.coherence_protocol import CoherenceProtocol
from gem5.components.boards.x86_board import X86Board
from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
    MESITwoLevelCacheHierarchy,
)
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.isas import ISA
from gem5.resources.resource import (
    CustomDiskImageResource,
    Resource,
)
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires

parser = argparse.ArgumentParser(
    description="Invoke a binary in FS mode, fast-forwarding to binary start and then optionally sampling (iteratively fast-forwards for ff_interval instructions, then switches to timing core and runs for warmup_interval instructions before collecting stats for roi_interval instructions)"
)
parser.add_argument(
    "--benchmark",
    required=True,
    type=str,
    choices=[
        # GAP
        "bc",
        "bfs",
        "cc",
        "pr",
        "sssp",
        "tc",
        # Parsec
        "blackscholes",
        "bodytrack",
        "canneal",
        "dedup",
        "facesim",
        "ferret",
        "fluidanimate",
        "freqmine",
        "raytrace",
        "streamcluster",
        "swaptions",
        "vips",
        "x264",
    ],
    help="The benchmark to simulate [REQUIRED]",
)
parser.add_argument(
    "--size",
    default="large",
    type=str,
    choices=["small", "medium", "large", "native"],
    help="Input size",
)
parser.add_argument("--cores", type=int, default=1, help="number of cores")
parser.add_argument(
    "--nokvm",
    default=False,
    action="store_true",
    help="use atomic core for fast-forwarding",
)
parser.add_argument(
    "--init_ff",
    type=int,
    help="fast-forward the first INIT_FF million instructions after benchmark start",
)
parser.add_argument(
    "--sample",
    default=False,
    action="store_true",
    help="run with periodic sampling",
)
parser.add_argument(
    "ff_interval",
    nargs="?",
    type=int,
    help="fast-forwarding interval, # of instructions in millions (required with --sample)",
)
parser.add_argument(
    "warmup_interval",
    nargs="?",
    type=int,
    help="warmup interval, # of instructions in millions (required with --sample)",
)
parser.add_argument(
    "roi_interval",
    nargs="?",
    type=int,
    help="ROI interval, # of instructions in millions (required with --sample)",
)
parser.add_argument(
    "--max_rois",
    type=int,
    help="in sample mode, stop sampling after MAX_ROIS ROIs (default: no max)",
)
parser.add_argument(
    "--continue",
    default=False,
    action="store_true",
    dest="continueSim",
    help="in sample mode, after MAX_ROIS ROIs, continue fast-forward execution (default: terminate)",
)
parser.add_argument(
    "--l2_replacement_policy",
    required=True,
    type=str,
    choices=[
        "TreePLRU",
        "LRU",
        "Random",
        "FIFO",
        "LFU",
        "MRU",
        "RPC",
        "CS395TRP",
        "SHIP",
    ],
    help="Replacement policy for the L2 cache",
)
args = parser.parse_args()

if args.sample:
    if (
        args.ff_interval is None
        or args.warmup_interval is None
        or args.roi_interval is None
    ):
        print(
            "Sample mode requires three positional args: ff_interval warmup_interval roi_interval"
        )
        sys.exit(1)
    if args.max_rois:
        if args.max_rois < 1:
            print("MAX_ROIS must be positive")
            sys.exit(1)
    else:
        if args.continueSim:
            print("--continue is only valid with --max_rois")
            sys.exit(1)
    args.ff_interval *= 1000000
    args.warmup_interval *= 1000000
    args.roi_interval *= 1000000
else:
    if args.ff_interval:
        print("A sample interval was specified but --sample omitted")
        sys.exit(1)
    if args.max_rois or args.continueSim:
        print(
            "Flags --max_rois and --continue are invalid without --sample mode"
        )
        sys.exit(1)
if args.init_ff:
    if args.init_ff < 1:
        print("INIT_FF must be positive")
        sys.exit(1)
    args.init_ff *= 1000000

# requires(
#     isa_required=ISA.X86,
#     coherence_protocol_required=CoherenceProtocol.MESI_TWO_LEVEL,
#     kvm_required=True
# )

# Setup the system memory
# (note: the X86 board supports only 3GB of main memory)
memory = DualChannelDDR4_2400(size="3GB")


replacement_policies = {
    "TreePLRU": TreePLRURP,
    "LRU": LRURP,
    "Random": RandomRP,
    "FIFO": FIFORP,
    "LFU": LFURP,
    "MRU": MRURP,
    "RPC": RPC,
    "CS395TRP": CS395TRP,
    "SHIP": SHiPRP,
}
l2_replacement_policy_class = replacement_policies.get(
    args.l2_replacement_policy, None
)
l2_replacement_policy = l2_replacement_policy_class()
print(
    "Using L2 replacement policy: {}".format(
        l2_replacement_policy_class.__name__
    )
)

# Set up the cache hierarchy
cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1i_size="32kB",
    l1i_assoc="4",
    l1d_size="32kB",
    l1d_assoc="4",
    l2_size="4MB",
    l2_assoc="8",
    num_l2_banks=1,
    # prefetch_enable=False
    l2_replacement_policy=l2_replacement_policy,
)

# Set up the processor (which contains some number of cores)
# A switchable processor will start simulation in the first processor
# and switch to the second on a call to processor.switch()
# In stats.txt, stats will be separated between processor.start.*
# and processor.switch.*
processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.KVM if not args.nokvm else CPUTypes.ATOMIC,
    switch_core_type=CPUTypes.O3,
    isa=ISA.X86,
    num_cores=args.cores,
)

# Set up the board.
board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Run command is copied into the disk image via readfile_contents and executed.
# Anything you want to run on a timing core should be wrapped in m5 workbegin/end.
# Your command should end in m5 exit; otherwise, simulation will drop to a shell
# prompt at the end rather than exiting Gem5.
if args.benchmark in ["bc", "bfs", "cc", "pr"]:
    if args.size == "small":
        inputName = "USA-road-d.COL.gr"
    elif args.size == "medium":
        inputName = "USA-road-d.CAL.gr"
    else:
        inputName = "USA-road-d.CTR.gr"
    benchmark_cmd = (
        "cd /home/gem5/gapbs;"
        f"./{args.benchmark} -n 1 -r 1 -f ../graphs/roads/{inputName};"
    )
elif args.benchmark in ["sssp"]:
    if args.size == "small":
        inputName = "g100k.wsg"
    elif args.size == "medium":
        inputName = "g1m.wsg"
    else:
        inputName = "g4m.wsg"
    benchmark_cmd = (
        "cd /home/gem5/gapbs;"
        f"./{args.benchmark} -n 1 -r 1 -f ../graphs/synth/{inputName};"
    )
elif args.benchmark in ["tc"]:
    if args.size == "small":
        inputName = "g100k.sg"
    elif args.size == "medium":
        inputName = "g500k.sg"
    else:
        inputName = "g1m.sg"
    benchmark_cmd = (
        "cd /home/gem5/gapbs;"
        f"./{args.benchmark} -n 1 -r 1 -f ../graphs/synth/{inputName};"
    )
else:
    if args.size == "native":
        inputName = "native"
    else:
        inputName = "sim" + args.size
    benchmark_cmd = (
        "cd /home/gem5/parsec-benchmark;"
        "source env.sh;"
        f"NTHREADS={8 * args.cores};"
        f"stdbuf -oL parsecmgmt -a run -p {args.benchmark} -c gcc-hooks -i {inputName} -n {8 * args.cores}"
        + " | stdbuf -oL tee /dev/fd/2"
        + ' | awk \'{print $0}; /\\[HOOKS\\] Entering ROI/ {print "ROI Begin Detected! Switching CPU..."; system(""); system("m5 workbegin")}\''
        + ' | awk \'{print $0}; /\\[HOOKS\\] Leaving ROI/ {print "ROI End Detected! Switching CPU..."; system(""); system("m5 workend")}\';'
    )

command = (
    "m5 workbegin;"
    + benchmark_cmd
    + "m5 workend;"
    + "sleep 5;"  # don't cut off output
    + "m5 exit;"
)

# If you leave the command str blank, the simulation will drop to a shell prompt
# and you can run any command you want, including executing benchmarks wrapped in
# workbegin/end, e.g.,:
#  "m5 workbegin; ./matmul_small; m5 workend;"
# (Caution: this doesn't always play nice with --sample mode.)
# To interact with the simulated shell prompt, build m5term and connect:
#    > cd gem5/util/term; make
#    > ./gem5/util/term/m5term localhost 3456

# Resource() attempts to download the kernel from gem5-resources if not
# already present in $GEM5_RESOURCES_DIR.
board.set_kernel_disk_workload(
    kernel=Resource("x86-linux-kernel-4.19.83"),
    # The second argument here tells Gem5 where the root partition is
    # This string will be appended to /dev/hda and used in the kernel command
    disk_image=CustomDiskImageResource(
        # local_path="/scratch/cluster/qduong/cs395t/hw1c/gem5/benchmarks_image",
        local_path="/scratch/cluster/speedway/gem5_resources/disk_images/gap-and-parsec-image/gap-and-parsec",
        root_partition="1",
    ),
    readfile_contents=command,
)


class Interval:
    NO_WORK = 1  # not even in benchmark
    FF_INIT = 2  # in initial FF window (--init_ff)
    FF_WORK = 3  # sampling FF interval
    WARMUP = 4  # sampling warmup interval
    ROI = 5  # sampling ROI interval


def switch_handler():
    global current_interval
    global start_time
    print(
        "***Switching to timing processor. Fast forward took {} seconds".format(
            time.time() - start_time
        )
    )
    start_time = time.time()
    processor.switch()
    current_interval = Interval.WARMUP
    # Schedule end of WARMUP interval
    simulator.schedule_max_insts(args.warmup_interval)


def workbegin_handler():
    global current_interval
    global completed_rois
    global start_tick
    global start_time

    num_entries = 0
    # Start of benchmark execution.
    while True:
        print(f"Num entries: {num_entries}")
        if num_entries <= 0:
            start_time = time.time()
            completed_rois = 0
            print("***Beginning benchmark execution")
            # Initial fast-forward set: no core switch, but set up next exit event
            if args.init_ff:
                print("***Beginning initial fast-forward")
                current_interval = Interval.FF_INIT
                simulator.schedule_max_insts(args.init_ff)
            # Sampling mode: Still fast-forwarding (no core switch), but set up
            # exit event for the end of our fast-forwarding window
            elif args.sample and current_interval != Interval.FF_WORK:
                current_interval = Interval.FF_WORK
                simulator.schedule_max_insts(args.ff_interval)
            # Whole-benchmark mode: Switch cores to timing and start wamrup/ROI
        elif num_entries == 1:
            switch_handler()
        else:
            print(
                "Error, too many workbegin entries, this should never happen"
            )

        num_entries += 1
        yield False  # continue .run()


def workend_handler():
    global current_interval
    global completed_rois
    global total_ticks
    global start_tick
    global start_time
    # Benchmark is over; dump final stats block if we're mid-ROI
    # and make sure we're back in the FF processor
    while True:
        print("***End of benchmark execution")
        if current_interval == Interval.ROI:
            print(
                "===Exiting stats ROI #{} at benchmark end. Took {} seconds".format(
                    completed_rois + 1, time.time() - start_time
                )
            )
            m5.stats.dump()
            end_tick = m5.curTick()
            total_ticks += end_tick - start_tick
            completed_rois += 1
        if current_interval in [Interval.ROI, Interval.WARMUP]:
            print("***Switching to fast-forward processor for post-benchmark")
            processor.switch()
        # Gem5 will always dump a final stats block when it exits, if any stats
        # have changed since the last one.  This means that we'll end up with an
        # annoying unwanted final stats block of non-ROI. At least zero it out.
        m5.stats.reset()
        current_interval = Interval.NO_WORK
        yield False  # continue .run(), we haven't seen an m5 exit yet


def maxinsts_handler():
    global current_interval
    global completed_rois
    global total_ticks
    global start_tick
    global start_time

    roi_inst_count = 0
    roi_inst_per_dump = min(args.roi_interval / (2 * args.cores), 50 * 1000000)

    while True:
        # ROI --> FF_WORK: end of ROI, dump stats and switch to FF processor
        if current_interval == Interval.ROI:
            if roi_inst_count < args.roi_interval:
                print("Recording stats (ROI not yet complete)")
                m5.stats.dump()
                m5.stats.reset()
                inst_to_run = int(
                    min(
                        roi_inst_per_dump,
                        abs(args.roi_interval - roi_inst_count),
                    )
                )
                print(f"scheduling {inst_to_run} insts")
                simulator.schedule_max_insts(inst_to_run)
                roi_inst_count += inst_to_run
            else:
                print(
                    "===Exiting stats ROI #{}. Took {} seconds".format(
                        completed_rois + 1, time.time() - start_time
                    )
                )
                m5.stats.dump()
                end_tick = m5.curTick()
                total_ticks += end_tick - start_tick
                completed_rois += 1
                print("***Switching to fast-forward processor")
                processor.switch()
                current_interval = Interval.FF_WORK
                # Schedule end of FF_WORK interval (if we're not out of max ROIs)
                if args.max_rois and completed_rois >= args.max_rois:
                    if args.continueSim:
                        print(
                            "***Max ROIs reached, fast-forwarding remainder of benchmark"
                        )
                    else:
                        print("***Max ROIs reached, terminating simulation")
                        m5.stats.reset()  # reset stats first, to handle unwanted final block
                        yield True  # terminate .run()
                else:
                    simulator.schedule_max_insts(args.ff_interval)
        # WARMUP --> ROI: end of warmup, reset stats and start ROI (proc already timing)
        elif current_interval == Interval.WARMUP:
            print(
                "===Entering stats ROI #{}. Warmup took {} seconds".format(
                    completed_rois + 1, time.time() - start_time
                )
            )
            m5.stats.reset()
            start_tick = m5.curTick()
            current_interval = Interval.ROI
            # Schedule end of ROI interval
            inst_to_run = int(
                min(roi_inst_per_dump, abs(args.roi_interval - roi_inst_count))
            )
            print(f"scheduling {inst_to_run} insts")
            simulator.schedule_max_insts(inst_to_run)
            roi_inst_count += inst_to_run
        else:
            print("Error, this should never happen")

        yield False  # continue .run()


# Set up simulator and define what happens on exit events
# using a custom generator
simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.WORKBEGIN: workbegin_handler(),
        ExitEvent.WORKEND: workend_handler(),
        ExitEvent.MAX_INSTS: maxinsts_handler(),
    },
)

total_ticks = 0
globalStart = time.time()

current_interval = (
    Interval.NO_WORK
)  # we start in fast-forward core, outside of benchmark
print("***Beginning simulation!")
simulator.run()

exit_cause = simulator.get_last_exit_event_cause()
if exit_cause == "m5_exit instruction encountered":
    print("***Exited simulation due to m5 exit")
elif (
    args.max_rois
    and not args.continueSim
    and exit_cause == "a thread reached the max instruction count"
):
    print("***Exited simulation due to max_rois met")
else:
    print(
        "***WARNING: Exited simulation due to unexpected cause: {}".format(
            exit_cause
        )
    )
print("Simulated ticks in ROIs: %.2f" % total_ticks)
print(
    "Total wallclock time: %.2f s = %.2f min"
    % (time.time() - globalStart, (time.time() - globalStart) / 60)
)
