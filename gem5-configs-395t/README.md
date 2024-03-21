# Gem5 Config Script Library

This is a library of configuration scripts and utilities for running Gem5 simulations in both full-system (FS) and syscall-emulation (SE) modes.

## Requirements

These directions assume you have a compiled version of Gem5's latest release (v22.1 or later!) in `$GEM5_HOME`.  You should also set an environment variable `$GEM5_RESOURCE_DIR` to wherever you want to store downloaded resources (e.g., built-in disk and kernel images).  Many of these examples also assume you're working on a machine with KVM.  Lastly, you're assumed to have read permission to `/scratch/cluster/speedway`, where shared Gem5 resources like disk images reside.

## Overview

Whenever you want to run a Gem5 simulation, you should begin by writing a ***top-level config script*** for the system and workload you want to simulate.  (Once upon a time, there were only two of these: the infamous `fs.py` and `se.py`, which you can still find in `$GEM5_HOME/configs/example/`.  These config scripts are deprecated!  They grew impractically large and complex and often don't do what they profess to).

Your top-level config script should instantiate all the components of the system you want to build (i.e., a processor composed of CPUs, a cache hierarchy, and some DDR) as well as define the workload you want to simulate.  For an SE simulation, this will include a binary and its arguments.  For an FS simulation, it will include a kernel image and disk image as well as the command(s) to run once the OS boots.  The top-level config script should also handle any configuration arguments you want to expose to the command line.

The gem5 standard library provides various Python wrappers intended to make it easier to configure and run simulations.  The libraries here expand the standard library further, modularizing common functionality in an attempt to promote reusability and make top-level config scripts very simple to write.

## Directory Structure

The top-level directory has various example top-level config scripts that you can use as templates for your desired simulation.  Before using one of them, pay attention to exactly what processor and cache hierarchy it's instantiating, what workload it's simulating, etc. and modify appropriately!  Here are a few that may be particularly useful:

- **se_custom_binary.py:**  In syscall emulation mode, run a binary (with arguments) specified on the command line on an out-of-order (O3) core model and 3-level classic cache hierarchy.
- **fs_spec06gap_with_sampling.py:**  In full system mode, run a single-threaded benchmark from the SPEC 2006 or GAP benchmark suites using periodic sampling, on an O3 core model and 3-level classic cache hierarchy.
- **fs_gapparsec.py:**  In full system mode, run a multi-threaded benchmark from the GAP or Parsec benchmark suites on a simple timing core and 3-level classic cache hierarchy, with number of cores specified by a `--cores N` command-line argument.
- **fs_post_boot_checkpoint.py:**  Boot the OS on an atomic fast core and create a post-boot checkpoint that can be restored from to run any arbitrary command.  You want this if you're working without KVM.
- **fs_gapparsec_take_checkpoints.py:**  On an atomic fast core, run a multithreaded GAP or Parsec benchmark (with `--cores N`) and create checkpoints every X million instructions through the parallel region-of-interest (ROI) annotated in the code.  This can be used to achieve periodic sampling without KVM (which doesn't support multithreading).  To accelerate the OS boot, you can start from a post-OS-boot checkpoint created with the config script above using the `--start_from` flag.
- **fs_restore_checkpoint.py**:  On an O3 core with 3-level classic cache hierarchy, restore a checkpoint (e.g., one created with the config script above) and simulate. Optionally, run for `--warmup Y` million instructions and then collect stats for `--roi Z` million instructions before terminating.

Running any of these top-level config scipts with `--help` will display all the command-line configuration options available for that script, e.g.:
```shell
> $GEM5_HOME/build/X86/gem5.opt gem5-configs/fs_hello_world.py --help
```

### components/

A handful of configurable CPU and cache hierarchy models you can instantiate in your top-level config script (as well as some processor models that extend those in the Gem5 standard library to be more useful).

* **components/cpus/**

  Provides an out-of-order (O3) CPU model based loosely on an Intel Skylake, in `skylake_cpu.py`.

  `simargs_o3_cpu.py` provides a command-line option to change the branch predictor of an O3 CPU.  Ideally, all O3 CPU models will incorporate this library; feel free to grow the list of configurable options it supports.

* **components/cache_hierarchies**

  Provides classic cache models for L1, L2, and LLC caches as well as an MMU cache for page table entries, in `classic_caches.py`.  Also provides `three_level_classic.py`, a 3-level cache hierarchy incorporating these caches into a system with a private L1D, private L1I, and private L2 per core plus a shared LLC.

  `simargs_cache_hierarchy.py` provides command-line options to change L1D, L1I, L2, and LLC cache sizes and associativities plus the prefetcher and cache replacement policy of each cache.  Ideally, all cache hierarchy models should incorporate this library; feel free to grow the list of configurable options it supports.

* **components/processors**

  Extensions of the gem5 stdlib core and processor wrappers to make core customization work better and support modularization of event handling.

### workloads/

Workloads for both FS and SE simulations.  `custom_workloads.py` provides parent classes `CustomSEWorkload` and `CustomFSWorkload` that all workloads should extend.  The `fs/` subdirectory contains various full-system workloads, including a hello-world and some simple test programs for verifying basic functionality of simulator changes, plus disk images for SPEC, GAP, and Parsec benchmarks.  The `se/` subdirectory contains a simple hello-world syscall emulation workload as well as a workload allowing command-line specification of a binary and its arguments.

### util/

Some useful libraries.

`simarglib.py` implements command-line arguments that are pooled between modules.  When you import a module that uses simarglib into your top-level configuration script, that module's sim arguments will be added to the `--help` menu automatically.  Please use this library for *all* simulation configuration arguments in any new modules you develop!

* **util/event_managers**

  Event handling libraries specifying what should happen on an m5 op (described in more detail in the Example Config Script section below).  These libraries can be used to implement simulation behavior like collecting statistics only for an ROI annotated in the program or run command with `m5 workbegin` and `m5 workend`, periodic sampling of ROIs with user-specified fast-forward, warmup, and stats-collection intervals, and checkpointing.
  
  `event_manager.py` provides a parent class `EventManager` that all event managers should extend.

## Example Config Script

Below we'll design the `fs_hello_world.py` example top-level config script as a demonstration of how to write your own.

First, import all Python, gem5, and local libraries needed by your design:

```python
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
from components.processors.custom_x86_switchable_processor import CustomX86SwitchableProcessor
from components.cache_hierarchies.three_level_classic import ThreeLevelClassicHierarchy
import util.simarglib as simarglib
from util.event_managers.simple_roi_manager import SimpleROIManager
from workloads.fs.hello_world import HelloWorldFS
```

Next, parse all command-line arguments (which are defined in the local modules imported above):

```python
# Parse all command-line args
simarglib.parse()
```

Instantiate the processor model (including core type), cache hierarchy model, and DDR model for the system you want to simulate:

```python
# Create a processor
requires(
    isa_required = ISA.X86
)

# Create a switchable processor
#
# Define start and switch core with --start_core_type
# # and --switch_core_type runtime knobs respectively
processor = CustomX86SwitchableProcessor(
    SwitchCPUCls = SkylakeCPU
)

# Create a cache hierarchy
cache_hierarchy = ThreeLevelClassicHierarchy()

# Create some DRAM
memory = DualChannelDDR4_2400(size="3GB")
```

The switchable processor begins simulation with a fast core model (in this case, KVM) and switches to a detailed core model on some ***m5 op*** -- a special hardware instruction inserted in the benchmark binary or included in the command executed on the simulated system that traps to the simulator.  SwitchCPUCls is an optional parameter that allows the switch to be to a custom core model (in this case, our SkylakeCPU) rather than to Gem5's built-in O3 core.

Next, create a board wiring together the components above, and instantiate the Workload you want to execute.

```python
# Create a board
board = X86Board(
    clk_freq = "3GHz",
    processor = processor,
    cache_hierarchy = cache_hierarchy,
    memory = memory
)

# Set up the workload
workload = HelloWorldFS()
board.set_workload(workload)
```

Then, create a Simulator object and configure the simulation:

```python
# Set up the simulator
# (including any event management)
manager = SimpleROIManager(processor)
simulator = Simulator(
    board = board,
    on_exit_event = manager.get_exit_event_handlers()
)
manager.initialize()
```

This is where you install the event manager you want, i.e., define what happens on various m5 ops.  Our GAP and Parsec disk image contains benchmarks that were compiled with m5 ops annotating their parallel ROIs.  For other benchmarks, the m5 utility is present in the disk image and you can surround your benchmark execution in `m5 workbegin` and `m5 workend` to denote the ROI (see the HelloWorldFS workload as an example).  The SimpleROIManager event manager (in `util/event_managers/simple_roi_manager.py`) uses these hooks to reset Gem5's statistics counters on workbegin and dump them to file on workend.  In other words, with this manager, `stats.txt` in your outdir will contain only the statistics for the benchmark itself.

Some event managers require  initialization steps before the simulation runs, so you should always call `manager.initialize()`.

Lastly, we run our simulation!  (And report anything we care about at the end.)

```python
# Run the simulation
starttime = time.time()
print("***Beginning simulation!")
simulator.run()

totaltime = time.time() - starttime
print(f"***Exiting @ tick {simulator.get_current_tick()} because {simulator.get_last_exit_event_cause()}.")
print(f"Total wall clock time: {totaltime:.2f} s = {(totaltime/60):.2f} min")
print(f"Simulated ticks in ROIs: {manager.get_total_ticks()}")
```

And that's it!

If you want to run a simulation using some other CPU or cache hierarchy, or a different event manager, or a different workload, just write a new top-level config script.  It will be identical to the above with just a few lines changed.

## Modifications and Extensions

This code is all lightly and imperfectly tested, so please feel free to fix any errors you come across!  You should also feel free to add any functionality you want, including new event managers and workloads.  Please try to keep your additions modular and geared toward enabling highly resuable, plug-and-play components for super-simple top-level config scripts.  Otherwise we'll quickly end up with our own in-house versions of fs.py and se.py... :-)

Here are some things I know we need...
- Ruby cache models configured similarly to the caches in `components/cache_hierarchies/caches/classic_caches.py`
- A Ruby 3-level cache hierarchy with private L1s and L2s and a shared LLC, ideally with a NUCA banked LLC structure and a realistic NoC
- More checkpoint creation and restoration managers, including ones that use the switchable processor and KVM before the ROI
