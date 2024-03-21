"""
This is a minor tweak to the gem5 stdlib's SimpleProcessor
(in src/python/gem5/components/processors/simple_processor.py)
This version just creates N CustomX86Cores (instead of SimpleCores),
allowing custom CPU models to be used.
It also moves some functionality around scheduling max insts
from the Simulator object to here, for event management convenience.
"""
from typing import Type

from m5.objects import BaseCPU
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA

from components.processors.custom_x86_core import CustomX86Core
import components.processors.simargs_processor as simargs

class CustomX86Processor(BaseCPUProcessor):
    def __init__(
        self, 
        CPUCls: Type[BaseCPU] = None
    ) -> None:
        proc_params = simargs.get_processor_params()
        num_cores = proc_params["cores"]
        core_type = proc_params["CoreCls"]
        if (not num_cores) or (num_cores <= 0):
            raise AssertionError("Number of cores must be a positive integer!")

        super().__init__(
            cores = [
                CustomX86Core(
                    core_id = i,
                    core_type = core_type,
                    CPUCls = CPUCls
                )
                for i in range(num_cores)
            ]
        )

        print(f"Creating X86 Processor: num_cores={num_cores}, core_type={core_type}")

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
