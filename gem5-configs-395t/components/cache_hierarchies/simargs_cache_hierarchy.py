"""
This is a simargs library for cache hierarchies composed of L1s, L2s,
and LLCs, allowing command-line customization of various cache params
(It currently supports changing cache size and associativity per level,
plus the prefetcher and replacement policy with limited options.
"""
from typing import Dict, Any

from m5.objects import (
    StridePrefetcher, SignaturePathPrefetcher, CS395TPrefetcher, # Prefetchers
    LRURP, TreePLRURP, CS395TRP, # Replacement policies
    NULL
)
import util.simarglib as simarglib

###
# PARSER CONFIGURATION
parser = simarglib.add_parser("Cache Hierarchy")

parser.add_argument("--l1d_size", type=str, help="L1 data size")
parser.add_argument("--l1d_assoc", type=int, help="L1 data associativity")
parser.add_argument("--l1d_pref", type=str, choices=["stride", "spp", "cs395t", "no"], help="L1 data prefetcher")
parser.add_argument("--l1d_repl", type=str, choices=["lru", "plru", "cs395t"], help="L1 data replacement policy")

parser.add_argument("--l1i_size", type=str, help="L1 inst size")
parser.add_argument("--l1i_assoc", type=int, help="L1 inst associativity")
parser.add_argument("--l1i_pref", type=str, choices=["stride", "spp", "cs395t", "no"], help="L1 inst prefetcher")
parser.add_argument("--l1i_repl", type=str, choices=["lru", "plru", "cs395t"], help="L1 inst replacement policy")

parser.add_argument("--l2_size", type=str, help="L2 size")
parser.add_argument("--l2_assoc", type=int, help="L2 associativity")
parser.add_argument("--l2_pref", type=str, choices=["stride", "spp", "cs395t", "no"], help="L2 prefetcher")
parser.add_argument("--l2_repl", type=str, choices=["lru", "plru", "cs395t"], help="L2 replacement policy")

parser.add_argument("--llc_size", type=str, help="LLC size")
parser.add_argument("--llc_assoc", type=int, help="LLC associativity")
parser.add_argument("--llc_pref", type=str, choices=["stride", "spp", "cs395t", "no"], help="LLC prefetcher")
parser.add_argument("--llc_repl", type=str, choices=["lru", "plru", "cs395t"], help="LLC replacement policy")
###

def get_l1d_params() -> Dict[str, Any]:
    params = {}

    if (simarglib.get("l1d_size")):
        params["size"] = simarglib.get("l1d_size")
    
    if (simarglib.get("l1d_assoc")):
        params["assoc"] = simarglib.get("l1d_assoc")
    
    if (simarglib.get("l1d_pref") == "stride"):
        params["PrefetcherCls"] = StridePrefetcher
        params["prefetcher_params"] = {
            "degree": 1
        }
    elif (simarglib.get("l1d_pref") == "spp"):
        params["PrefetcherCls"] = SignaturePathPrefetcher
        params["prefetcher_params"] = {}
    elif (simarglib.get("l1d_pref") == "cs395t"):
        params["PrefetcherCls"] = CS395TPrefetcher
        params["prefetcher_params"] = {
            "size": 2048
        }
        # You can either read parameters from the command line
        # (by adding more parser.add_argument calls) or
        # hardcode the parameters you want here.
        # TODO: Add more params here (or process them)
        #
        # You'll have to repeat this for each cache.

    elif (simarglib.get("l1d_pref") == "no"):
        params["PrefetcherCls"] = NULL
        params["prefetcher_params"] = {}

    if (simarglib.get("l1d_repl") == "lru"):
        params["ReplacementPolicyCls"] = LRURP
        params["replacement_params"] = {}
    elif (simarglib.get("l1d_repl") == "plru"):
        params["ReplacementPolicyCls"] = TreePLRURP
        params["replacement_params"] = {}
    elif (simarglib.get("l1d_repl") == "cs395t"):
        params["ReplacementPolicyCls"] = CS395TRP
        params["replacement_params"] = {
            "size": 2048
        }
        # You can either read parameters from the command line
        # (by adding more parser.add_argument calls) or
        # hardcode the parameters you want here.
        # TODO: Add more params here (or process them)
        #
        # You'll have to repeat this for each cache.
    
    return params

def get_l1i_params() -> Dict[str, Any]:
    params = {}

    if (simarglib.get("l1i_size")):
        params["size"] = simarglib.get("l1i_size")
    
    if (simarglib.get("l1i_assoc")):
        params["assoc"] = simarglib.get("l1i_assoc")
    
    if (simarglib.get("l1i_pref") == "stride"):
        params["PrefetcherCls"] = StridePrefetcher
        params["prefetcher_params"] = {
            "degree": 1
        }
    elif (simarglib.get("l1i_pref") == "spp"):
        params["PrefetcherCls"] = SignaturePathPrefetcher
        params["prefetcher_params"] = {}
    elif (simarglib.get("l1i_pref") == "cs395t"):
        params["PrefetcherCls"] = CS395TPrefetcher
        params["prefetcher_params"] = {
            "size": 2048
        }
    elif (simarglib.get("l1i_pref") == "no"):
        params["PrefetcherCls"] = NULL
        params["prefetcher_params"] = {}
    
    if (simarglib.get("l1i_repl") == "lru"):
        params["ReplacementPolicyCls"] = LRURP
        params["replacement_params"] = {}
    elif (simarglib.get("l1i_repl") == "plru"):
        params["ReplacementPolicyCls"] = TreePLRURP
        params["replacement_params"] = {}
    elif (simarglib.get("l1i_repl") == "cs395t"):
        params["ReplacementPolicyCls"] = CS395TRP
        params["replacement_params"] = {
            "size": 2048
        }
    
    return params

def get_l2_params() -> Dict[str, Any]:
    params = {}

    if (simarglib.get("l2_size")):
        params["size"] = simarglib.get("l2_size")
    
    if (simarglib.get("l2_assoc")):
        params["assoc"] = simarglib.get("l2_assoc")
    
    if (simarglib.get("l2_pref") == "stride"):
        params["PrefetcherCls"] = StridePrefetcher
        params["prefetcher_params"] = {
            "degree": 1
        }
    elif (simarglib.get("l2_pref") == "spp"):
        params["PrefetcherCls"] = SignaturePathPrefetcher
        params["prefetcher_params"] = {}
    elif (simarglib.get("l2_pref") == "cs395t"):
        params["PrefetcherCls"] = CS395TPrefetcher
        params["prefetcher_params"] = {
            "size": 2048
        }
    elif (simarglib.get("l2_pref") == "no"):
        params["PrefetcherCls"] = NULL
        params["prefetcher_params"] = {}
    
    if (simarglib.get("l2_repl") == "lru"):
        params["ReplacementPolicyCls"] = LRURP
        params["replacement_params"] = {}
    elif (simarglib.get("l2_repl") == "plru"):
        params["ReplacementPolicyCls"] = TreePLRURP
        params["replacement_params"] = {}
    elif (simarglib.get("l2_repl") == "cs395t"):
        params["ReplacementPolicyCls"] = CS395TRP
        params["replacement_params"] = {
            "size": 2048
        }
    
    return params

def get_llc_params() -> Dict[str, Any]:
    params = {}

    if (simarglib.get("llc_size")):
        params["size"] = simarglib.get("llc_size")
    
    if (simarglib.get("llc_assoc")):
        params["assoc"] = simarglib.get("llc_assoc")
    
    if (simarglib.get("llc_pref") == "stride"):
        params["PrefetcherCls"] = StridePrefetcher
        params["prefetcher_params"] = {
            "degree": 1
        }
    elif (simarglib.get("llc_pref") == "spp"):
        params["PrefetcherCls"] = SignaturePathPrefetcher
        params["prefetcher_params"] = {}
    elif (simarglib.get("llc_pref") == "cs395t"):
        params["PrefetcherCls"] = CS395TPrefetcher
        params["prefetcher_params"] = {
            "size": 2048
        }
    elif (simarglib.get("llc_pref") == "no"):
        params["PrefetcherCls"] = NULL
        params["prefetcher_params"] = {}
    
    if (simarglib.get("llc_repl") == "lru"):
        params["ReplacementPolicyCls"] = LRURP
        params["replacement_params"] = {}
    elif (simarglib.get("llc_repl") == "plru"):
        params["ReplacementPolicyCls"] = TreePLRURP
        params["replacement_params"] = {}
    elif (simarglib.get("llc_repl") == "cs395t"):
        params["ReplacementPolicyCls"] = CS395TRP
        params["replacement_params"] = {
            "size": 2048
        }
    
    return params
