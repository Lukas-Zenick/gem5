"""
Restores simulation from a given checkpoint and runs for X million warmup
instructions and then collects ROI stats for Y million instructions.
No processor switching, so restore should be with a detailed timing core

To be used with restore_checkpoint.py workload!
"""
import sys
from typing import Dict, Generator

import m5
from gem5.simulate.exit_event import ExitEvent
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor

from util.event_managers.event_manager import EventManager
import util.simarglib as simarglib

###
# PARSER CONFIGURATION
parser = simarglib.add_parser("Checkpoint Restore")
parser.add_argument("--warmup", type=int, help="Warm up for WARMUP million instructions after restore")
parser.add_argument("--roi", type=int, help="Simulate and record stats for ROI million instructions after warmup")
###

class RestoreCheckpointManager(EventManager):
    def __init__(self, processor : BaseCPUProcessor) -> None:
        super().__init__(processor = processor)

        self._warmup = simarglib.get("warmup")
        self._roi = simarglib.get("roi")

        if self._warmup:
            if (self._warmup < 0):
                print("WARMUP must be non-negative!")
                sys.exit(1)
            self._warmup *= 1000000
        else:
            self._warmup = 0

        if self._roi:
            if (self._roi < 1):
                print("ROI must be positive!")
                sys.exit(1)
            self._roi *= 1000000
        else:
            self._roi = 0

    def initialize(self) -> None:
        # need to set up initial max insts interrupts and start ROI if we're
        # not in warmup. board is not initialized yet, so must pass a flag
        # to that effect to schedule_max_insts()!
        if (self._warmup > 0):
            self._processor.schedule_max_insts(self._warmup, core0_only=True,
                                               already_running=False)
        else:
            self._start_tick = m5.curTick()
            print("===Entering ROI at restore")
            m5.stats.reset()
            if (self._roi > 0):
                self._processor.schedule_max_insts(self._roi, core0_only=True, 
                                                   already_running=False)

    """
    handler dictionary
    """
    def get_exit_event_handlers(self) -> Dict[ExitEvent, Generator]:
        return {
            ExitEvent.WORKEND : self.handle_workend(),
            ExitEvent.MAX_INSTS : self.handle_maxinsts()
        }

    """
    workend:
    """
    def handle_workend(self):
        end_tick = m5.curTick()
        self._total_ticks += (end_tick - self._start_tick)
        print("===Exiting ROI at workend")
        m5.stats.dump()
        m5.stats.reset()
        yield True # terminate simulation

    """
    maxinsts:
    """
    def handle_maxinsts(self):
        if (self._warmup > 0):
            # first max_insts will be end of warmup
            self._start_tick = m5.curTick()
            print("===Entering ROI at end of warmup")
            m5.stats.reset()
            if (self._roi > 0):
                self._processor.schedule_max_insts(self._roi, core0_only=True)
            yield False
        # second max_insts will be end of ROI
        print("===Exiting ROI after max insts")
        m5.stats.dump()
        m5.stats.reset()
        yield True # terminate simulation
