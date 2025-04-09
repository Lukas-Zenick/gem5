#!/usr/bin/env python3

"""
run_fs_mesi_two_level_multithread.py

Example gem5 Python configuration script for a full-system, Ruby MESI Two-Level
cache simulation that supports multi-threading (SMT), sampling (fast-forward,
warmup, ROI intervals), and dynamic L2 replacement policies.

This script is intentionally written to demonstrate:
1) Using the Ruby MESI Two-Level protocol from the gem5 Standard Library.
2) Setting up multi-threading by enabling board.multi_thread = True.
3) Switching from a fast-forward CPU (KVM or Atomic) to O3 for ROI stats.
4) Handling multiple intervals (fast-forward, warmup, ROI) in the same run.
5) Setting a user-specified L2 replacement policy for the Ruby L2.

You can adapt or simplify as needed.
"""

import argparse
import sys
import time

import m5
from m5.objects import (
    CS395TRP,
    FIFORP,
    LFURP,
    LRURP,
    MRURP,
    RPC,
    RandomRP,
    TreePLRURP,
)

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

###############################################################################
# 1. Parse Arguments
###############################################################################

parser = argparse.ArgumentParser(
    description="Run a Ruby MESI 2-Level FS simulation w/ multi-threading & sampling."
)

parser.add_argument(
    "--benchmark",
    required=True,
    type=str,
    help="Name of the benchmark inside the disk image.",
)
parser.add_argument(
    "--size",
    default="medium",
    choices=["small", "medium", "large", "native"],
    help="Input size or parsec size (if using parsec).",
)

parser.add_argument(
    "--physical_cores",
    type=int,
    default=1,
    help="Number of physical CPU cores (for O3).",
)
parser.add_argument(
    "--threads_per_core",
    type=int,
    default=1,
    help="Hardware threads (SMT) per core (O3). If >1, multi_thread must be enabled.",
)
parser.add_argument(
    "--nokvm",
    action="store_true",
    default=False,
    help="Use Atomic for fast-forward instead of KVM.",
)
parser.add_argument(
    "--init_ff",
    type=int,
    default=0,
    help="Initial fast-forward (millions of instructions) after benchmark start, before any sampling.",
)
parser.add_argument(
    "--sample",
    action="store_true",
    default=False,
    help="Enable sampling-based simulation with repeated intervals of FF->WARMUP->ROI.",
)
parser.add_argument(
    "ff_interval",
    nargs="?",
    type=int,
    help="Fast-forward interval, in millions of instructions (required if --sample).",
)
parser.add_argument(
    "warmup_interval",
    nargs="?",
    type=int,
    help="Warmup interval, in millions of instructions (required if --sample).",
)
parser.add_argument(
    "roi_interval",
    nargs="?",
    type=int,
    help="ROI interval, in millions of instructions (required if --sample).",
)
parser.add_argument(
    "--max_rois",
    type=int,
    default=0,
    help="Stop after this many ROI intervals, or 0=unlimited (only relevant with --sample).",
)
parser.add_argument(
    "--continue",
    dest="continue_sim",
    action="store_true",
    default=False,
    help="If --max_rois is set, continue fast-forward after the last ROI instead of exiting.",
)
parser.add_argument(
    "--l2_replacement_policy",
    required=True,
    type=str,
    help="L2 replacement policy: e.g. LRU, FIFO, Random, etc.",
)

args = parser.parse_args()

# Basic validation
if args.sample:
    if (
        (args.ff_interval is None)
        or (args.warmup_interval is None)
        or (args.roi_interval is None)
    ):
        print(
            "ERROR: --sample requires three positional intervals: ff_interval warmup_interval roi_interval"
        )
        sys.exit(1)
else:
    if (
        (args.ff_interval is not None)
        or (args.warmup_interval is not None)
        or (args.roi_interval is not None)
    ):
        print("ERROR: sample intervals were specified without --sample.")
        sys.exit(1)

if args.max_rois < 0:
    print("ERROR: --max_rois must be >= 0.")
    sys.exit(1)

if (not args.sample) and (args.continue_sim):
    print("ERROR: --continue only makes sense with --sample.")
    sys.exit(1)

###############################################################################
# 2. Setup Memory and L2 Replacement
###############################################################################

# Convert million instructions to absolute instructions
init_ff_insts = args.init_ff * 1_000_000 if args.init_ff else 0
if args.sample:
    ff_insts = args.ff_interval * 1_000_000
    warmup_insts = args.warmup_interval * 1_000_000
    roi_insts = args.roi_interval * 1_000_000
else:
    ff_insts = 0
    warmup_insts = 0
    roi_insts = 0

# Dictionary of known L2 replacement policy classes.
# Update this mapping to match your actual gem5 build or Python imports.
rp_map = {
    "TreePLRU": TreePLRURP,
    "LRU": LRURP,
    "Random": RandomRP,
    "FIFO": FIFORP,
    "LFU": LFURP,
    "MRU": MRURP,
    "RPC": RPC,
    "CS395TRP": CS395TRP,
}

if args.l2_replacement_policy not in rp_map:
    print(
        f"ERROR: Unknown L2 replacement policy '{args.l2_replacement_policy}'."
    )
    sys.exit(1)

chosen_rp_class = rp_map[args.l2_replacement_policy]
chosen_rp = chosen_rp_class()

print(f"[INFO] Using L2 replacement policy: {args.l2_replacement_policy}")

# Create the Ruby MESI two-level hierarchy
cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1i_size="32kB",
    l1i_assoc="4",
    l1d_size="32kB",
    l1d_assoc="4",
    l2_size="4MB",
    l2_assoc="8",
    num_l2_banks=1,
    l2_replacement_policy=chosen_rp,
)

# Set up the main memory
memory = DualChannelDDR4_2400(size="3GB")

###############################################################################
# 3. Configure the Processor (Switchable) & Board
###############################################################################

# We will use a switchable processor: fast-forward on KVM or ATOMIC, then switch to O3.
starting_cpu_type = CPUTypes.KVM if not args.nokvm else CPUTypes.ATOMIC
o3_cpu_type = CPUTypes.O3

# Number of total logical cores = physical_cores * threads_per_core
num_logical_cores = args.physical_cores * args.threads_per_core

processor = SimpleSwitchableProcessor(
    starting_core_type=starting_cpu_type,
    switch_core_type=o3_cpu_type,
    isa=ISA.X86,
    num_cores=num_logical_cores,
)

# Create X86 board
board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Enable multi-threading (SMT). This allows each "core" to have multiple thread contexts.
# In the Standard Library, setting board.multi_thread=True signals the system to
# share an L1 (and other per-core resources) among threads. If your gem5 version
# doesn’t support that boolean, check the code to see how it’s implemented.
board.multi_thread = True

###############################################################################
# 4. Setting the Workload & Command
###############################################################################

# This is an example using the parsec environment.
# It will call 'm5 workbegin' at ROI start, 'm5 workend' at ROI end, then 'm5 exit'.
# Modify as appropriate for your own disk image or your desired commands.

# guest_cmd = f"""
#     echo "=== Starting {args.benchmark} with input size {args.size} ===";
#     cd /home/gem5/parsec-benchmark;
#     source env.sh;
#     export OMP_NUM_THREADS={num_logical_cores};
#     # Enter the ROI
#     m5 workbegin;
#     parsecmgmt -a run -p {args.benchmark} -c gcc-hooks -i sim{args.size} -n {num_logical_cores};
#     m5 workend;
#     m5 exit;
# """

guest_cmd = f"""
    echo "=== Starting {args.benchmark} with input size {args.size} ===";
    cd /home/gem5/parsec-benchmark;
    source env.sh;
    export OMP_NUM_THREADS={num_logical_cores};
    # Enter the ROI
    parsecmgmt -a run -p {args.benchmark} -c gcc-hooks -i sim{args.size} -n {num_logical_cores};
    m5 exit;
"""

# Point to your kernel/disk image resources. If you have a custom disk, specify it:
board.set_kernel_disk_workload(
    kernel=Resource("x86-linux-kernel-4.19.83"),  # Example kernel
    disk_image=CustomDiskImageResource(
        local_path="/scratch/cluster/speedway/gem5_resources/disk_images/gap-and-parsec-image/gap-and-parsec",
        root_partition="1",
    ),
    readfile_contents=guest_cmd,
)

###############################################################################
# 5. Define the Event Handling for Sampling
###############################################################################


class Interval:
    NO_WORK = 0
    INIT_FF = 1
    FF = 2
    WARMUP = 3
    ROI = 4


current_interval = Interval.NO_WORK
rois_completed = 0

# We'll track simulation ticks in ROI if you like:
roi_tick_start = 0
total_roi_ticks = 0

start_time_wallclock = time.time()


def handle_workbegin():
    """
    We entered the ROI region in the guest (via 'm5 workbegin').
    If user wants an initial fast-forward, do that. Otherwise, switch to the next stage.
    """
    global current_interval
    # If this is the first time we see a 'workbegin', do initial FF if set
    if current_interval == Interval.NO_WORK:
        if init_ff_insts > 0:
            print(
                f"** Starting initial fast-forward of {init_ff_insts} instructions."
            )
            current_interval = Interval.INIT_FF
            # simulator.schedule_max_insts(init_ff_insts)
        elif args.sample:
            print("** Starting sampling-based fast-forward interval.")
            current_interval = Interval.FF
            # simulator.schedule_max_insts(ff_insts)
        else:
            # No sampling, no initial FF. Switch to O3 right away
            print("** Switching immediately to O3 CPU (no FF).")
            processor.switch()
            current_interval = Interval.ROI
    else:
        print(
            "WARNING: 'workbegin' called, but we're already in an interval!?"
        )

    yield False  # Keep running


def handle_workend():
    """
    We reached the ROI end in the guest. Usually that means the benchmark is done.
    If we were in an ROI interval, finish up stats, and switch to FF CPU again.
    """
    global current_interval, rois_completed, total_roi_ticks, roi_tick_start

    if current_interval == Interval.ROI:
        # Dump stats for the ROI we just completed
        rois_completed += 1
        print(f"** Completed ROI #{rois_completed}. Dumping stats.")
        m5.stats.dump()
        m5.stats.reset()
        total_roi_ticks += m5.curTick() - roi_tick_start

        # Switch to FF CPU
        processor.switch()
        current_interval = (
            Interval.NO_WORK
        )  # or go back to fast-forward if more ROI is possible
        print(
            "** ROI ended, presumably the entire benchmark ended as well (parsec typically does one ROI)."
        )
    else:
        print(
            "** Workend encountered, but we were not in ROI interval? Possibly the benchmark is finishing anyway."
        )

    yield False


def handle_maxinsts():
    """
    We hit a scheduled instruction limit. Decide what the next step is.
    """
    global current_interval, rois_completed, roi_tick_start, total_roi_ticks

    if current_interval in [Interval.INIT_FF, Interval.FF]:
        # We finished a FF chunk, switch to O3 and do warmup or ROI
        print("** Done with fast-forward chunk. Switching to O3 CPU.")
        processor.switch()

        if args.sample:
            if current_interval == Interval.INIT_FF:
                # After init FF, go to FF interval (start sampling)
                current_interval = Interval.FF
                # simulator.schedule_max_insts(ff_insts)
            else:
                # We finished the normal FF chunk in a sample iteration
                current_interval = Interval.WARMUP
                # simulator.schedule_max_insts(warmup_insts)
        else:
            # No sampling => we’re ready for the ROI
            current_interval = Interval.ROI
    elif current_interval == Interval.WARMUP:
        # We just finished warmup. Start ROI
        print("** Entering an ROI interval. Reset stats, then go!")
        m5.stats.reset()
        roi_tick_start = m5.curTick()
        current_interval = Interval.ROI
        # simulator.schedule_max_insts(roi_insts)
    elif current_interval == Interval.ROI:
        # We just finished an ROI chunk. Dump stats, switch to FF if continuing
        rois_completed += 1
        print(f"** Completed ROI #{rois_completed}. Dumping stats.")
        m5.stats.dump()
        m5.stats.reset()
        total_roi_ticks += m5.curTick() - roi_tick_start

        # If we have a max_rois limit, check if we should stop
        if args.max_rois > 0 and rois_completed >= args.max_rois:
            if args.continue_sim:
                print(
                    "** Max ROI reached, but continuing with fast-forward (no more stats)."
                )
                processor.switch()
                current_interval = Interval.FF
                # simulator.schedule_max_insts(ff_insts)
            else:
                print("** Max ROI reached, ending simulation now.")
                yield True  # signals to the simulator to exit
        else:
            # Go back to fast-forward => next iteration
            print("** Switching to fast-forward CPU for next iteration.")
            processor.switch()
            current_interval = Interval.FF
            # simulator.schedule_max_insts(ff_insts)
    else:
        print(
            "** Unexpected interval state on maxinsts. Possibly end of simulation."
        )
    yield False


###############################################################################
# 6. Setup Simulator
###############################################################################

simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.WORKBEGIN: handle_workbegin(),
        ExitEvent.WORKEND: handle_workend(),
        ExitEvent.MAX_INSTS: handle_maxinsts(),
    },
)

print("** Beginning simulation now!")
simulator.run()

exit_cause = simulator.get_last_exit_event_cause()
print(f"** Exiting simulation. Exit cause: {exit_cause}")

print(f"** Completed {rois_completed} ROI intervals total.")
print(f"** Total ROI ticks: {total_roi_ticks}")
wallclock_elapsed = time.time() - start_time_wallclock
print(
    f"** Total wallclock time: {wallclock_elapsed:.2f} seconds ({wallclock_elapsed/60:.2f} min)"
)
