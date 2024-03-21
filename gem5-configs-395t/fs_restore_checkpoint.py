"""
Sample FS config script to restore a checkpoint with a detailed O3 processor
and a three-level classic cache hierarchy, and run for an optional number of
warmup and ROI-length instructions
"""
import time

import m5
from m5.objects import *
from gem5.utils.requires import requires
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory import DualChannelDDR4_2400
from gem5.isas import ISA
from gem5.components.processors.cpu_types import CPUTypes
from gem5.simulate.simulator import Simulator

from components.cpus.skylake_cpu import SkylakeCPU
from components.processors.custom_x86_processor import CustomX86Processor
from components.cache_hierarchies.three_level_classic import ThreeLevelClassicHierarchy
import util.simarglib as simarglib
from util.event_managers.restore_checkpoint_manager import RestoreCheckpointManager
from workloads.fs.restore_checkpoint import RestoreCheckpointFS

# Parse all command-line args
simarglib.parse()

# Create a processor
requires(
    isa_required = ISA.X86
)

# O3 core type recommended
processor = CustomX86Processor(
    CPUCls = SkylakeCPU
)

# Create a cache hierarchy
cache_hierarchy = ThreeLevelClassicHierarchy()

# Create some DRAM
memory = DualChannelDDR4_2400(size="3GB")

# Create a board
board = X86Board(
    clk_freq = "3GHz",
    processor = processor,
    cache_hierarchy = cache_hierarchy,
    memory = memory
)

# Set up the workload
workload = RestoreCheckpointFS()
board.set_workload(workload)

# Set up the simulator
# (including any event management)
manager = RestoreCheckpointManager(processor)
simulator = Simulator(
    board = board,
    on_exit_event = manager.get_exit_event_handlers()
)
manager.initialize()

# Run the simulation
starttime = time.time()
print("***Beginning simulation!")
simulator.run()

totaltime = time.time() - starttime
print(f"***Exiting @ tick {simulator.get_current_tick()} because {simulator.get_last_exit_event_cause()}.")
print(f"Total wall clock time: {totaltime:.2f} s = {(totaltime/60):.2f} min")
print(f"Simulated ticks in ROIs: {manager.get_total_ticks()}")
