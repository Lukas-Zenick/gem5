"""
Sample FS config script to run multi-threaded GAP and Parsec benchmarks
on a fast ATOMIC CPU, optionally from a post-OS-boot checkpoint, and
creating checkpoints at intervals throughout the benchmark ROI
"""
import time

import m5
from m5.objects import *
from gem5.utils.requires import requires
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.cachehierarchies.classic.no_cache import NoCache
from gem5.isas import ISA
from gem5.components.processors.cpu_types import CPUTypes
from gem5.simulate.simulator import Simulator

from components.processors.custom_x86_processor import CustomX86Processor
import util.simarglib as simarglib
from util.event_managers.take_checkpoints_manager import TakeCheckpointsManager
from workloads.fs.gap_and_parsec import GapAndParsecFS

# Parse all command-line args
simarglib.parse()

# Create a processor (atomic for checkpointing)
requires(
    isa_required = ISA.X86
)

# Atomic core type recommended
processor = CustomX86Processor()

# Create a cache hierarchy (none for checkpointing)
cache_hierarchy = NoCache()

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
workload = GapAndParsecFS()
board.set_workload(workload)

# Set up the simulator
# (including any event management)
manager = TakeCheckpointsManager(processor)
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
