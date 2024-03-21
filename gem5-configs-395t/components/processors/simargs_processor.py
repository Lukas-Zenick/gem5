"""
This is a simargs library for configuring a Processor,
allowing command-line customization of Processor params,
e.g., the number of cores
"""
from typing import Dict, Any

from gem5.components.processors.cpu_types import CPUTypes

import util.simarglib as simarglib

###
# PARSER CONFIGURATION
parser = simarglib.add_parser("Processor")
parser.add_argument("--cores", type=int, default=1, help="Processor core count")
parser.add_argument("--core_type", type=str, default="o3", help="Core type",
                    choices=["atomic", "kvm", "minor", "o3", "timing"])
###

def get_processor_params() -> Dict[str, Any]:
    params = {}

    if simarglib.get("cores"):
        params["cores"] = simarglib.get("cores")

    if simarglib.get("core_type") == "atomic":
        params["CoreCls"] = CPUTypes.ATOMIC
    elif simarglib.get("core_type") == "kvm":
        params["CoreCls"] = CPUTypes.KVM
    elif simarglib.get("core_type") == "minor":
        params["CoreCls"] = CPUTypes.MINOR
    elif simarglib.get("core_type") == "o3":
        params["CoreCls"] = CPUTypes.O3
    elif simarglib.get("core_type") == "timing":
        params["CoreCls"] = CPUTypes.TIMING

    return params
