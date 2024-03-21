"""
Sets up periodic sampling management, allowing for a simulation to
be fastforwarded for an inital interval, then stepped through intervals
of X million insts of fast-forward, switch to timing proc, Y million 
insts of warmup, Z million insts of ROI with stats collection, switch back
"""
import sys
import time
from typing import Dict, Generator
from enum import Enum

import m5
from gem5.simulate.exit_event import ExitEvent
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor

from util.event_managers.event_manager import EventManager
import util.simarglib as simarglib

###
# PARSER CONFIGURATION
parser = simarglib.add_parser("Periodic Sampling")
parser.add_argument("--ff", required=True, type=int, help="Fast-forwarding interval between ROIs, in millions of instructions [REQUIRED]")
parser.add_argument("--warmup", required=True, type=int, help="Warmup interval before ROIs, in millions of instructions [REQUIRED]")
parser.add_argument("--roi", required=True, type=int, help="ROI length in millions of instructions [REQUIRED]")
parser.add_argument("--init_ff", type=int, help="Fast-forward the first INIT_FF million instructions after benchmark start")
parser.add_argument("--max_rois", type=int, help="Stop sampling after MAX_ROIS ROIs (default: no max)")
parser.add_argument("--continue", default=False, action="store_true", help="After MAX_ROIs reached, continue fast-forward execution (default: terminate)")
###

class Interval(Enum):
    NO_WORK = 1 # not even in benchmark yet
    FF_INIT = 2 # initial FF window
    FF_WORK = 3 # sampling FF interval
    WARMUP = 4  # sampling warmup interval
    ROI = 5     # sampling ROI interval

class SamplingManager(EventManager):
    def __init__(self, processor : BaseCPUProcessor) -> None:
        super().__init__(processor = processor)

        # we start in FF core, outside of benchmark
        self._current_interval = Interval.NO_WORK

        self._ff_interval = simarglib.get("ff")
        if (self._ff_interval < 0):
            print("FF interval cannot be negative!")
            sys.exit(1)
        self._ff_interval *= 1000000

        self._warmup_interval = simarglib.get("warmup")
        if (self._warmup_interval < 0):
            print("WARMUP interval cannot be negative!")
            sys.exit(1)
        self._warmup_interval *= 1000000

        self._roi_interval = simarglib.get("roi")
        if (self._roi_interval < 0):
            print("ROI length cannot be negative!")
            sys.exit(1)
        self._roi_interval *= 1000000
        
        self._init_ff = simarglib.get("init_ff")
        if self._init_ff:
            if (self._init_ff < 1):
                print("INIT_FF interval must be positive!")
                sys.exit(1)
            self._init_ff *= 1000000

        self._maxRois = simarglib.get("max_rois")
        if self._maxRois:
            if (self._maxRois < 1):
                print("MAX_ROIS must be positive!")
                sys.exit(1)

        self._continueSim = simarglib.get("continue")

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
    workbegin
    """
    def handle_workbegin(self):
        while True:
            self._completed_rois = 0
            print("***Beginning benchmark execution")
            if (self._init_ff):
                # Initial fast-forward set: no core switch, but set up next exit event
                print("***Beginning initial fast-forward")
                self._current_interval = Interval.FF_INIT
                self._processor.schedule_max_insts(self._init_ff, core0_only=True)
            else:
                # No initial FF, we should start sampling iterations
                self._current_interval = Interval.FF_WORK
                self._processor.schedule_max_insts(self._ff_interval, core0_only=True)
            self._start_time = time.time()
            yield False
    
    """
    workend
    """
    def handle_workend(self):
        while True:
            print("***End of benchmark execution")
            if (self._current_interval == Interval.ROI):
                # We're mid-ROI, dump stats block
                print(f"===Exiting stats ROI #{self._completed_rois + 1} at benchmark end."
                      f" Took {round(time.time()-self._start_time, 2)} seconds")
                m5.stats.dump()
                end_tick = m5.curTick()
                self._total_ticks += (end_tick - self._start_tick)
                self._completed_rois += 1
            if (self._current_interval in [Interval.ROI, Interval.WARMUP]):
                # We're mid-ROI or mid-warmup
                print("***Switching to fast-forward processor for post-benchmark")
                self._processor.switch()
            # Gem5 will always dump an annoying final stats block when it
            # exits, if any stats have changed since last one. Zero it, anyway
            m5.stats.reset()
            self._current_interval = Interval.NO_WORK
            yield False

    """
    maxinsts
    """
    def handle_maxinsts(self):
        while True:
            # ROI -> FF_WORK: end of ROI, dump stats and switch to FF proc
            if (self._current_interval == Interval.ROI):
                print(f"===Exiting stats ROI #{self._completed_rois + 1}."
                      f" Took {round(time.time()-self._start_time, 2)} seconds")
                m5.stats.dump()
                end_tick = m5.curTick()
                self._total_ticks += (end_tick - self._start_tick)
                self._completed_rois += 1

                print("***Switching to fast-forward processor")
                self._processor.switch()
                self._current_interval = Interval.FF_WORK

                # schedule end of FF_WORK interval (if we're not out of MAX_ROIs)
                if (self._maxRois and self._completed_rois >= self._maxRois):
                    if (self._continueSim):
                        print("***Max ROIs reached, fast-forwarding remainder of benchmark")
                    else:
                        print("***Max ROIs reached, terminating simulation")
                        m5.stats.reset() # clear unwanted final stats block
                        yield True # terminate .run()
                else:
                    self._processor.schedule_max_insts(self._ff_interval, core0_only=True)
            
            # WARMUP -> ROI: end of warmup, reset stats and start ROI
            elif (self._current_interval == Interval.WARMUP):
                print(f"===Entering stats ROI #{self._completed_rois + 1}."
                      f" Warmup took {round(time.time()-self._start_time, 2)} seconds")
                m5.stats.reset()
                self._start_tick = m5.curTick()
                self._current_interval = Interval.ROI
                # schedule end of ROI interval
                self._processor.schedule_max_insts(self._roi_interval, core0_only=True)

            # FF_WORK -> WARMUP: end of fast-forward, switch processors and enter warmup
            elif (self._current_interval == Interval.FF_WORK):
                print("***Switching to timing processor (end of fast-forward interval)")
                self._processor.switch()
                self._current_interval = Interval.WARMUP
                # schedule end of WARMUP interval
                self._processor.schedule_max_insts(self._warmup_interval, core0_only=True)

            # FF_INIT -> FF_WORK: done with init, begin ff/warmup/roi iteration
            elif (self._current_interval == Interval.FF_INIT):
                print(f"***End of initial fast-forward. Took {round(time.time()-self._start_time, 2)} seconds")
                self._current_interval = Interval.FF_WORK
                # schedule end of FF_WORK interval
                self._processor.schedule_max_insts(self._ff_interval, core0_only=True)

            # else: current_interval == Interval.NO_WORK: nothing to do!
            # (this occurs if workend arrived mid-sample-interval, leaving one schedule maxinsts)

            self._start_time = time.time()
            yield False
