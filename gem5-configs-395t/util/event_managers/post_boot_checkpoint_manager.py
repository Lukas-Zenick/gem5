"""
Takes a post-OS boot checkpoint and then exits

To be used in combination with the take_boot_checkpoint.py workload!
"""
from typing import Dict, Generator
from pathlib import Path

import m5
from gem5.simulate.exit_event import ExitEvent
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor

from util.event_managers.event_manager import EventManager
import util.simarglib as simarglib

###
# PARSER CONFIGURATION
parser = simarglib.add_parser("Post-OS Boot Checkpointing")
parser.add_argument("--checkpoint_dir", type=str, default="boot_checkpoint",
                    help="Post-OS-boot checkpoint dir (default: boot_checkpoint/)")
###

class PostBootCheckpointManager(EventManager):
    def __init__(self, processor : BaseCPUProcessor) -> None:
        super().__init__(processor = processor)
        self._chkptDir = Path(simarglib.get("checkpoint_dir"))
        self._chkptDir.mkdir(parents = True, exist_ok = True)

    """
    handler dictionary
    """
    def get_exit_event_handlers(self) -> Dict[ExitEvent, Generator]:
        return {
            ExitEvent.CHECKPOINT : self.handle_checkpoint()
        }

    """
    checkpoint:
    """
    def handle_checkpoint(self):
        print("###Taking post-OS-boot checkpoint")
        m5.checkpoint(str(self._chkptDir))
        yield True # terminate simulation
