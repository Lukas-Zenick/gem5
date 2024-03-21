"""
Sets up checkpoint creation at periodic intervals during the simulation of
a program (presumably on a fast core, to be restored on a more detailed model)
"""
import sys
from typing import Dict, Generator
from pathlib import Path

import m5
from gem5.simulate.exit_event import ExitEvent
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor

from util.event_managers.event_manager import EventManager
import util.simarglib as simarglib

###
# PARSER CONFIGURATION
parser = simarglib.add_parser("Periodic Checkpointing")
parser.add_argument("--interval", required=True, type=int, help="Create checkpoint at start of ROI and every INTERVAL million instructions (on core 0) until end of ROI [REQUIRED]")
parser.add_argument("--checkpoints_dir", type=str, default="checkpoints", help="The enclosing directory in which to store checkpoint dirs (default: checkpoints/)")
parser.add_argument("--max_checkpoints", type=int, help="Stop after MAX_CHECKPOINTS checkpoints")
###

class TakeCheckpointsManager(EventManager):
    def __init__(self, processor : BaseCPUProcessor) -> None:
        super().__init__(processor = processor)
        
        # count checkpoints taken
        self._checkpoint_num = 0

        self._interval = simarglib.get("interval")
        self._checkpoints_dir = simarglib.get("checkpoints_dir")
        self._max_checkpoints = simarglib.get("max_checkpoints")

        if self._interval:
            if (self._interval < 1):
                print("INTERVAL must be positive!")
                sys.exit(1)
            self._interval *= 1000000
        else:
            self._interval = 0

        # Create enclosing checkpoint directory
        self._chkptDir = Path(self._checkpoints_dir)
        self._chkptDir.mkdir(parents = True, exist_ok = True)

    """
    handler dictionary
    """
    def get_exit_event_handlers(self) -> Dict[ExitEvent, Generator]:
        return {
            ExitEvent.WORKBEGIN : self.handle_workbegin(),
            ExitEvent.WORKEND : self.handle_workend(),
            ExitEvent.MAX_INSTS : self.handle_maxinsts()
        }

    """
    workend:
    """
    def handle_workend(self):
        end_tick = m5.curTick()
        self._total_ticks += (end_tick - self._start_tick)
        print("===Exiting ROI")
        m5.stats.dump()
        m5.stats.reset()
        yield True # terminate simulation

    """
    workbegin:
    """
    def handle_workbegin(self):
        self._start_tick = m5.curTick()
        print("===Entering ROI")
        m5.stats.reset()
        print(f"###Taking checkpoints every {self._interval} instructions")
        self._checkpoint_num += 1
        checkpoint = (self._chkptDir / f"chkpt.{str(self._start_tick)}").as_posix()
        print(f"###Checkpoint 1 (start of ROI): {checkpoint}")
        m5.checkpoint(str(checkpoint))
        # If we have more checkpoints to take, keep going, otherwise we're done
        if not self._max_checkpoints or (self._checkpoint_num < self._max_checkpoints):
            self._processor.schedule_max_insts(self._interval, core0_only=True)
            yield False
        else:
            yield True
    
    """
    maxinsts:
    """
    def handle_maxinsts(self):
        while True:
            self._checkpoint_num += 1
            checkpoint = (self._chkptDir / f"chkpt.{str(m5.curTick())}").as_posix()
            print(f"###Checkpoint {self._checkpoint_num}: {checkpoint}")
            m5.checkpoint(str(checkpoint))
            # If we have more checkpoints to take, keep going, otherwise we're done
            if not self._max_checkpoints or (self._checkpoint_num < self._max_checkpoints):
                self._processor.schedule_max_insts(self._interval, core0_only=True)
                yield False
            else:
                yield True
