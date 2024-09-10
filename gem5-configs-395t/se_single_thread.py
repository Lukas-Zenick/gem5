import time

from components.cache_hierarchies.three_level_classic import (
    ThreeLevelClassicHierarchy,
)
from components.cpus.skylake_cpu import SkylakeCPU
from components.processors.custom_x86_switchable_processor import (
    CustomX86SwitchableProcessor,
)

import util.simarglib as simarglib
from util.event_managers.sampling_manager import SamplingManager

import m5
from m5.objects import *

from gem5.components.boards.x86_board import X86Board
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import (
    DiskImageResource,
    Resource,
    obtain_resource,
)
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires

# Parse all command-line args
simarglib.parse()

# Ensure the gem5 binary supports the required ISA and other features.
requires(
    isa_required=ISA.X86,
)

# KVM start core, O3 switch core recommended
processor = CustomX86SwitchableProcessor(
    SwitchCPUCls=SkylakeCPU,
)

command = (
    "echo 'This is running on multi CPU cores.';"
    + "sleep 1;"
    + "cd /bin/;"
    + "sleep 1;"
    + "pwd;"
    + "sleep 2;"
    + "ls;"
    + "sleep 2;"
    + "chmod 700 ./multithread;"
    + "sleep 2;"
    + "./multithread;"
    + "sleep 2;"
    + "m5 exit;"
)

# Create a cache hierarchy
cache_hierarchy = ThreeLevelClassicHierarchy()

# Create some DRAM
memory = DualChannelDDR4_2400(size="3GB")

# Create a board
board = X86Board(
    clk_freq="4GHz",  # Using 4 GHz to match Skylake config from Assignment 1A.
    processor=processor,
    cache_hierarchy=cache_hierarchy,
    memory=memory,
)

# Set up the workload in Full-System mode
board.set_kernel_disk_workload(
    kernel=Resource("x86-linux-kernel-5.4.49"),
    # disk_image=Resource("x86-ubuntu-18.04-img"),
    # disk_image=Resource("raw-img"),
    disk_image=DiskImageResource(
        "/scratch/cluster/lukas/gem5_resources/raw-img", root_partition="1"
    ),
    readfile_contents=command,
)

# Set up the simulator and event management
manager = SamplingManager(processor)
simulator = Simulator(
    board=board, on_exit_event=manager.get_exit_event_handlers()
)
manager.initialize()

# Run the simulation
starttime = time.time()
print("***Beginning simulation!")
simulator.run()

# Print out timing and exit information
totaltime = time.time() - starttime
print(
    f"***Exiting @ tick {simulator.get_current_tick()} because {simulator.get_last_exit_event_cause()}."
)
print(f"Total wall clock time: {totaltime:.2f} s = {(totaltime/60):.2f} min")
print(f"Simulated ticks in ROIs: {manager.get_total_ticks()}")
