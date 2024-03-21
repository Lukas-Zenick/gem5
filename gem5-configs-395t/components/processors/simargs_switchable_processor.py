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
parser = simarglib.add_parser("Switchable Processor")
parser.add_argument("--cores", type=int, default=1, help="Processor core count")
parser.add_argument("--start_core_type", type=str, default="kvm", help="Start core type",
                    choices=["atomic", "kvm", "minor", "o3", "timing"])
parser.add_argument("--switch_core_type", type=str, default="timing", help="Switch core type",
                    choices=["atomic", "kvm", "minor", "o3", "timing"])
###

def get_switchable_processor_params() -> Dict[str, Any]:
    params = {}

    if simarglib.get("cores"):
        params["cores"] = simarglib.get("cores")

    if simarglib.get("start_core_type") == "atomic":
        params["StartCoreCls"] = CPUTypes.ATOMIC
    elif simarglib.get("start_core_type") == "kvm":
        params["StartCoreCls"] = CPUTypes.KVM
    elif simarglib.get("start_core_type") == "minor":
        params["StartCoreCls"] = CPUTypes.MINOR
    elif simarglib.get("start_core_type") == "o3":
        params["StartCoreCls"] = CPUTypes.O3
    elif simarglib.get("start_core_type") == "timing":
        params["StartCoreCls"] = CPUTypes.TIMING

    if simarglib.get("switch_core_type") == "atomic":
        params["SwitchCoreCls"] = CPUTypes.ATOMIC
    elif simarglib.get("switch_core_type") == "kvm":
        params["SwitchCoreCls"] = CPUTypes.KVM
    elif simarglib.get("switch_core_type") == "minor":
        params["SwitchCoreCls"] = CPUTypes.MINOR
    elif simarglib.get("switch_core_type") == "o3":
        params["SwitchCoreCls"] = CPUTypes.O3
    elif simarglib.get("switch_core_type") == "timing":
        params["SwitchCoreCls"] = CPUTypes.TIMING

    return params
