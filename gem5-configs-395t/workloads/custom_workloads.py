"""
Parent classes for FS and SE workloads
"""
from gem5.resources.resource import WorkloadResource
import util.simarglib as simarglib

###
# PARSER CONFIGURATION
parser = simarglib.add_parser("Workload")
parser.add_argument("--start_from", type=str, help="Start simulation from a checkpoint in dir START_FROM")
###

class CustomSEWorkload(WorkloadResource):
    """
    Legal parameters for SE workloads: (see components/boards/se_binary_workload.py)
      binary: AbstractResource  <-- REQUIRED
      arguments: List[str] = []
      checkpoint: Union[Path, AbstractResource] = None
      stdin_file: AbstractResource = None
      stdout_file: Path = None
      stderr_file: Path = None
      exit_on_work_items: bool = True
    """
    def __init__(self, **kwargs) -> None:
        super().__init__(
            function = "set_se_binary_workload",
            parameters = kwargs
        )

class CustomFSWorkload(WorkloadResource):
    """
    Legal parameters for FS workloads: (see components/boards/kernel_disk_workload.py)
      kernel: AbstractResource  <-- REQUIRED
      disk_image: AbstractResource  <-- REQUIRED
      readfile: str = None
      readfile_contents: str = None
      checkpoint: Union[Path, AbstractResource] = None
      bootloader: AbstractResource = None
      kernel_args: List[str] = None
      exit_on_work_items: bool = True
    """
    def __init__(self, **kwargs) -> None:
        super().__init__(
            function = "set_kernel_disk_workload",
            parameters = kwargs
        )
