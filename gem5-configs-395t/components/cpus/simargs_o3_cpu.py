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
    "--bpred", type=str, choices=["tage", "perceptron", "tournament", "cs395t"], default="tage",
    help="The CPU's branch predictor (default: tage)"
)
###

def get_cpu_params() -> Dict[str, Any]:
    params = {}

    if (simarglib.get("bpred") == "tage"):
        params["bpred_type"] = "TAGE"
        params["bpred_params"] = {}
    elif (simarglib.get("bpred") == "perceptron"):
        params["bpred_type"] = "Perceptron"
        params["bpred_params"] = {}
    elif (simarglib.get("bpred") == "tournament"):
        params["bpred_type"] = "Tournament"
        params["bpred_params"] = {}
    elif (simarglib.get("bpred") == "cs395t"):
        params["bpred_type"] = "CS395T"

        # You can either read parameters from the command line
        # (by adding more parser.add_argument calls) or
        # hardcode the parameters you want here.
        # TODO: Add more params here (or process them).
        params["bpred_params"] = {
            "size": 8192
        }

    return params
