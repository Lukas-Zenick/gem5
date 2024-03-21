"""
This is a simargs library for cache hierarchies composed of L1s, L2s,
and LLCs, allowing command-line customization of various cache params
(It currently supports changing cache size and associativity per level,
plus the prefetcher and replacement policy with limited options.
"""
from typing import Dict, Any

from m5.objects import (
    StridePrefetcher, SignaturePathPrefetcher,
    LRURP, TreePLRURP, NULL
)
import util.simarglib as simarglib

###
# PARSER CONFIGURATION
parser = simarglib.add_parser("Cache Hierarchy")

parser.add_argument("--l1d_size", type=str, help="L1 data size")
parser.add_argument("--l1d_assoc", type=int, help="L1 data associativity")
parser.add_argument("--l1d_pref", type=str, choices=["stride", "spp", "no"], help="L1 data prefetcher")
parser.add_argument("--l1d_repl", type=str, choices=["lru", "plru"], help="L1 data replacement policy")

parser.add_argument("--l1i_size", type=str, help="L1 inst size")
parser.add_argument("--l1i_assoc", type=int, help="L1 inst associativity")
parser.add_argument("--l1i_pref", type=str, choices=["stride", "spp", "no"], help="L1 inst prefetcher")
parser.add_argument("--l1i_repl", type=str, choices=["lru", "plru"], help="L1 inst replacement policy")

parser.add_argument("--l2_size", type=str, help="L2 size")
parser.add_argument("--l2_assoc", type=int, help="L2 associativity")
parser.add_argument("--l2_pref", type=str, choices=["stride", "spp", "no"], help="L2 prefetcher")
parser.add_argument("--l2_repl", type=str, choices=["lru", "plru"], help="L2 replacement policy")

parser.add_argument("--llc_size", type=str, help="LLC size")
parser.add_argument("--llc_assoc", type=int, help="LLC associativity")
parser.add_argument("--llc_pref", type=str, choices=["stride", "spp", "no"], help="LLC prefetcher")
parser.add_argument("--llc_repl", type=str, choices=["lru", "plru"], help="LLC replacement policy")
###

def get_l1d_params() -> Dict[str, Any]:
    params = {}

    if (simarglib.get("l1d_size")):
        params["size"] = simarglib.get("l1d_size")
    
    if (simarglib.get("l1d_assoc")):
        params["assoc"] = simarglib.get("l1d_assoc")
    
    if (simarglib.get("l1d_pref") == "stride"):
        params["PrefetcherCls"] = StridePrefetcher
    elif (simarglib.get("l1d_pref") == "spp"):
        params["PrefetcherCls"] = SignaturePathPrefetcher
    elif (simarglib.get("l1d_pref") == "no"):
        params["PrefetcherCls"] = NULL
    
    if (simarglib.get("l1d_repl") == "lru"):
        params["ReplacementPolicyCls"] = LRURP
    elif (simarglib.get("l1d_repl") == "plru"):
        params["ReplacementPolicyCls"] = TreePLRURP
    
    return params

def get_l1i_params() -> Dict[str, Any]:
    params = {}

    if (simarglib.get("l1i_size")):
        params["size"] = simarglib.get("l1i_size")
    
    if (simarglib.get("l1i_assoc")):
        params["assoc"] = simarglib.get("l1i_assoc")
    
    if (simarglib.get("l1i_pref") == "stride"):
        params["PrefetcherCls"] = StridePrefetcher
    elif (simarglib.get("l1i_pref") == "spp"):
        params["PrefetcherCls"] = SignaturePathPrefetcher
    elif (simarglib.get("l1i_pref") == "no"):
        params["PrefetcherCls"] = NULL
    
    if (simarglib.get("l1i_repl") == "lru"):
        params["ReplacementPolicyCls"] = LRURP
    elif (simarglib.get("l1i_repl") == "plru"):
        params["ReplacementPolicyCls"] = TreePLRURP
    
    return params

def get_l2_params() -> Dict[str, Any]:
    params = {}

    if (simarglib.get("l2_size")):
        params["size"] = simarglib.get("l2_size")
    
    if (simarglib.get("l2_assoc")):
        params["assoc"] = simarglib.get("l2_assoc")
    
    if (simarglib.get("l2_pref") == "stride"):
        params["PrefetcherCls"] = StridePrefetcher
    elif (simarglib.get("l2_pref") == "spp"):
        params["PrefetcherCls"] = SignaturePathPrefetcher
    elif (simarglib.get("l2_pref") == "no"):
        params["PrefetcherCls"] = NULL
    
    if (simarglib.get("l2_repl") == "lru"):
        params["ReplacementPolicyCls"] = LRURP
    elif (simarglib.get("l2_repl") == "plru"):
        params["ReplacementPolicyCls"] = TreePLRURP
    
    return params

def get_llc_params() -> Dict[str, Any]:
    params = {}

    if (simarglib.get("llc_size")):
        params["size"] = simarglib.get("llc_size")
    
    if (simarglib.get("llc_assoc")):
        params["assoc"] = simarglib.get("llc_assoc")
    
    if (simarglib.get("llc_pref") == "stride"):
        params["PrefetcherCls"] = StridePrefetcher
    elif (simarglib.get("llc_pref") == "spp"):
        params["PrefetcherCls"] = SignaturePathPrefetcher
    elif (simarglib.get("llc_pref") == "no"):
        params["PrefetcherCls"] = NULL
    
    if (simarglib.get("llc_repl") == "lru"):
        params["ReplacementPolicyCls"] = LRURP
    elif (simarglib.get("llc_repl") == "plru"):
        params["ReplacementPolicyCls"] = TreePLRURP
    
    return params
