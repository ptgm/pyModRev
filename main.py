"""
This script analyzes a given network model to determine its consistency.
If inconsistencies are found, it attempts to compute the minimal set of repair
operations needed to restore consistency.
"""

import argparse
import sys
import os
import inspect
import logging

from importlib import util
from typing import List, Dict
from network.network import Network
from parsers.reader_factory import get_reader
from configuration import config
from updaters.async_updater import AsyncUpdater
from updaters.sync_updater import SyncUpdater
from updaters.steady_state_updater import SteadyStateUpdater
from updaters.complete_updater import CompleteUpdater
from repair.engine import model_revision

# Configure logger
logger = logging.getLogger(__name__)


def process_arguments(network: Network) -> None:
    """
    Process command-line arguments and configure network accordingly.
    """
    parser = argparse.ArgumentParser(
        description="Model Revision program. Given a model and a set of observations, it determines if the model is consistent. If not, it computes all the minimum number of repair operations in order to render the model consistent.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Version: {config.version}"
    )

    parser.add_argument("-m", "--model", required=True, help="Input model file.")
    parser.add_argument("-obs", "--observations", nargs='+', required=True, metavar=('OBS', 'UPDATER'), help="List of observation file and updater pairs. Each observation must be followed by its updater type. Example: -obs obs1.lp asyncupdater obs2.lp syncupdater")
    parser.add_argument("-cc", "--check-consistency", action="store_true", help="Check the consistency of the model and return without repairing. DEFAULT: false.")
    parser.add_argument("--exhaustive-search", action="store_true", help="Force exhaustive search of function repair operations. DEFAULT: false.")
    parser.add_argument("--sub-opt", action="store_true", help="Show sub-optimal solutions found. DEFAULT: false.")
    parser.add_argument("-v", "--verbose", type=int, choices=[0, 1, 2, 3], default=2, help="Verbose level {0,1,2,3} of output. DEFAULT: 2.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")
    # parser.add_argument("--support", "-su", action="store_true", help="Support values for each variable.") # Not used in old logic

    args = parser.parse_args()

    # Apply arguments to config and network
    network.input_file_network = args.model
    config.check_consistency = args.check_consistency
    config.force_optimum = args.exhaustive_search
    config.show_solution_for_each_inconsistency = args.sub_opt
    config.verbose = args.verbose
    config.debug = args.debug

    # Activate debug mode
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s: %(message)s')
    
    obs_args = args.observations
    if len(obs_args) % 2 != 0:
        parser.error("Expected an even number of arguments for --observations (pairs of obs_file and updater_name)")

    for i in range(0, len(obs_args), 2):
        obs_path = obs_args[i]
        updater_name = obs_args[i+1]
        
        network.add_observation_file(obs_path)
        
        try:
            if updater_name.lower() != SteadyStateUpdater.__name__.lower():
                network.has_ts_obs = True
                if updater_name.lower() == SyncUpdater.__name__.lower():
                    network.add_updater_name('SyncUpdater')
                elif updater_name.lower() == AsyncUpdater.__name__.lower():
                    network.add_updater_name('AsyncUpdater')
                elif updater_name.lower() == CompleteUpdater.__name__.lower():
                    network.add_updater_name('CompleteUpdater')
                else:
                    raise Exception(f"Unknown non-steady state updater type encountered: {updater_name}")
                
                if len(network.updaters_name) > 1:
                    raise Exception(f"Conflicting updater types detected: {', '.join(network.updaters_name)} cannot coexist.")
            else:
                network.has_ss_obs = True

            updater_dir = os.path.join(os.path.dirname(__file__), "updaters")
            found_updater = False
            for filename in os.listdir(updater_dir):
                if filename.endswith(".py") and filename != "__init__.py":
                    file_path = os.path.join(updater_dir, filename)
                    classes = load_classes_from_file(file_path)
                    for name, cls in classes.items():
                        if updater_name.lower() == name.lower():
                            updater = cls()
                            network.add_updater(updater)
                            found_updater = True
                            break
                    if found_updater:
                        break
            
            if not found_updater:
                raise Exception(f"Updater '{updater_name}' not found in updaters directory")

        except Exception as e:
            parser.error(str(e))


def load_classes_from_file(file_path: str) -> Dict:
    """
    Dynamically loads classes from a Python file.
    """
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = util.spec_from_file_location(module_name, file_path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {name: cls for name, cls in inspect.getmembers(module, inspect.isclass)}


if __name__ == '__main__':
    network = Network()
    process_arguments(network)
    
    # Delegate parsing to the correct reader based on file extension
    try:
        reader = get_reader(network.input_file_network)
        parse = reader.read(network, network.input_file_network)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    if parse < 1 and not config.ignore_warnings:
        logger.error('Model definition with errors. Check documentation for input definition details.')
    else:
        model_revision(network)
