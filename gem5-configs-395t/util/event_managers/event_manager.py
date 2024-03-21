"""
Parent class for all event managers with some functions
that must be overridden
"""
from typing import Dict, Generator
from gem5.simulate.exit_event import ExitEvent
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor

class EventManager:
    def __init__(self, processor : BaseCPUProcessor) -> None:
        self._processor = processor
        # count ticks in ROIs
        self._total_ticks = 0

    def get_total_ticks(self) -> int:
        return self._total_ticks

    def initialize(self) -> None:
        pass

    """ handler dictionary """
    """ must be overridden by child class """
    def get_exit_event_handlers(self) -> Dict[ExitEvent, Generator]:
        return { }
