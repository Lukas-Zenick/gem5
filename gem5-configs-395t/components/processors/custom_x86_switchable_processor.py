"""
This is a minor tweak to the gem5 stdlib's SimpleSwitchableProcessor
(in src/python/gem5/components/processors/simple_switchable_processor.py)
This version just allows customization of the CPU model.
It also moves some functionality around scheduling max insts
from the Simulator object to here, for event management convenience.
"""
from typing import Optional, Type

from m5.objects import BaseCPU
from m5.util import warn
from gem5.components.boards.mem_mode import MemMode
from gem5.components.boards.abstract_board import AbstractBoard
from gem5.components.processors.cpu_types import CPUTypes, get_mem_mode
from gem5.components.processors.switchable_processor import SwitchableProcessor
from gem5.isas import ISA
from gem5.utils.override import *

from components.processors.custom_x86_core import CustomX86Core
import components.processors.simargs_switchable_processor as simargs

class CustomX86SwitchableProcessor(SwitchableProcessor):
    """
    A Simplified implementation of SwitchableProcessor where there is one
    processor at the start of the simulation and another that can be switched
    to via the "switch" function later in the simulation. This is good for
    fast/detailed CPU setups.
    """

    def __init__(
        self,
        StartingCPUCls: Type[BaseCPU] = None,
        SwitchCPUCls: Type[BaseCPU] = None
    ) -> None:
        """
        :param starting_core_type: The CPU type for each type in the processor
        to start with (i.e., when the simulation has just started).

        :param switch_core_types: The CPU type for each core, to be switched
        to..
        """
        proc_params = simargs.get_switchable_processor_params()
        num_cores = proc_params["cores"]
        starting_core_type = proc_params["StartCoreCls"]
        switch_core_type = proc_params["SwitchCoreCls"]

        if (not num_cores) or (num_cores <= 0):
            raise AssertionError("Number of cores must be a positive integer!")

        self._start_key = "start"
        self._switch_key = "switch"
        self._current_is_start = True

        self._mem_mode = get_mem_mode(starting_core_type)

        switchable_cores = {
            self._start_key: [
                CustomX86Core(
                    core_id = i,
                    core_type = starting_core_type,
                    CPUCls = StartingCPUCls
                )
                for i in range(num_cores)
            ],
            self._switch_key: [
                CustomX86Core(
                    core_id = i, 
                    core_type = switch_core_type,
                    CPUCls = SwitchCPUCls
                )
                for i in range(num_cores)
            ],
        }

        super().__init__(
            switchable_cores=switchable_cores, starting_cores=self._start_key
        )

        print(f"Creating X86 Switchable Processor: num_cores={num_cores}, start_core_type={starting_core_type}, switch_core_type={switch_core_type}")

    @overrides(SwitchableProcessor)
    def incorporate_processor(self, board: AbstractBoard) -> None:
        super().incorporate_processor(board=board)

        board.set_mem_mode(self._mem_mode)

    def switch(self):
        """Switches to the "switched out" cores."""
        if self._current_is_start:
            self.switch_to_processor(self._switch_key)
        else:
            self.switch_to_processor(self._start_key)

        self._current_is_start = not self._current_is_start
    
    # Simulator also has a schedule_max_insts() function, which just
    # loops through all the cores in self._board.get_processor().get_cores()
    # Moving this here, because it's not convenient to give event managers
    # a reference to the simulator object. (And also because I'm convinced
    # we may sometimes want to set max insts on one core, not all, e.g.,
    # for multi-threaded codes)
    def schedule_max_insts(
        self, insts: int, 
        core0_only: bool = False, 
        already_running: bool = True
    ) -> None:
        for core in self.get_cores():
            core._set_inst_stop_any_thread(insts, already_running)
            if core0_only:
                break
