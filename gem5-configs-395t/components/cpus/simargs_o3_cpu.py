"""
This is a simargs library for configuring an O3 CPU, allowing 
command-line customization of various of the CPU params
(It supports only branch predictor customization for now, but
could be expanded)
"""
from typing import Dict, Any
import inspect
import util.simarglib as simarglib

###
# PARSER CONFIGURATION
parser = simarglib.add_parser("O3 CPU")
parser.add_argument(
    "--bpred", type=str, choices=["tage", "perceptron", "tournament"], default="tage",
    help="The CPU's branch predictor (default: tage)"
)
###

def get_cpu_params() -> Dict[str, Any]:
    params = {}

    if (simarglib.get("bpred") == "tage"):
        params["bpred_type"] = "TAGE"
    elif (simarglib.get("bpred") == "perceptron"):
        params["bpred_type"] = "Perceptron"
    elif (simarglib.get("bpred") == "tournament"):
        params["bpred_type"] = "Tournament"

    return params
