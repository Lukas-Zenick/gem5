"""
Library implementing shared argparsing between modules, with each
module able to add its own argument group.  If arguments conflict,
bad things will happen.  No attempt is made to fix this! :-)
Based on: https://www.doc.ic.ac.uk/~nuric/coding/
argparse-with-multiple-files-to-handle-configuration-in-python.html
"""
import argparse
from typing import Dict, Any

# Global parser
parser = argparse.ArgumentParser("Gem5 Simulation Arguments")

# Global table of parsed args
args: Dict[str, Any] = {}

def add_parser(group_name: str, description: str = ""):
    """ Add a module's argument group and return the group """
    return parser.add_argument_group(group_name, description)

def parse() -> Dict[str, Any]:
    """ Parse all collected arguments """
    args.update(vars(parser.parse_args()))
    return args

def get(key: str):
    return args.get(key)

def set_component_parameters(component, params: dict, parent_name: str = ""):
    for param in params:
        prefix = f'[{parent_name}] ' if parent_name else ''
        print(f"{prefix}Setting {type(component).__name__} parameter \"{param}\" to {params[param]}")
        setattr(component, param, params[param])