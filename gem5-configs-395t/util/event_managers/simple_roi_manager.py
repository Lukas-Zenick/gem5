"""
Sets up simple ROI handling: on any m5 workbegin, switch CPU and
begin collecting stats; on any m5 workend, cease stat collection
and switch back to fast-forward processor
"""
from typing import Dict, Generator

import m5
from gem5.simulate.exit_event import ExitEvent
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor

from util.event_managers.event_manager import EventManager

class SimpleROIManager(EventManager):
    def __init__(self, processor : BaseCPUProcessor) -> None:
        super().__init__(processor = processor)

    """ handler dictionary """
    def get_exit_event_handlers(self) -> Dict[ExitEvent, Generator]:
        return {
            ExitEvent.WORKBEGIN : self.handle_workbegin(),
            ExitEvent.WORKEND : self.handle_workend()
        }

    def handle_workbegin(self):
        while True:
            self._start_tick = m5.curTick()
            print("***Switching to timing processor")
            self._processor.switch()
        
            print("===Entering ROI")
            m5.stats.reset()
            yield False
    
    def handle_workend(self):
        while True:
            end_tick = m5.curTick()
            self._total_ticks += (end_tick - self._start_tick)
            print("===Exiting ROI")
            m5.stats.dump()
            m5.stats.reset()
            print("***Switching to fast-forward processor")
            self._processor.switch()
            yield False
