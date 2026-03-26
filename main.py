"""
This script analyzes a given network model to determine its consistency.
If inconsistencies are found, it attempts to compute the minimal set of repair
operations needed to restore consistency.
"""

import argparse
import sys
import os
import logging

from importlib import util
from network.network import Network
from parsers.parser_factory import get_parser
from configuration import config
from repair.engine import model_revision
from repair.consistency import check_consistency
from repair.engine import print_consistency
from repair.repair import apply_repair

# Configure logger
logger = logging.getLogger(__name__)


def process_arguments(network: Network) -> None:
    """
    Process command-line arguments and configure network accordingly.
    """
    parser = argparse.ArgumentParser(
        description="Model Revision program. Given a model and a set of observations, it determines if the model is consistent. If not, it computes all the minimum number of repair operations in order to render the model consistent.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=f"Version: {config.version}"
    )

    parser.add_argument("-m", "--model",
                        required=True, help="Input model file.")
    parser.add_argument("-obs", "--observations", nargs='+',
                        required=True, metavar=('OBS', 'UPDATER'),
                        help="""List of observation files and updater pairs.
Each observation must be followed by its updater type. 
Example: -obs obs1.lp asyncupdater obs2.lp syncupdater""")
    parser.add_argument('-t', '--task', choices=['c', 'r', 'm'], required=True,
                        help="""Specify the task to perform (default=r):
   c - check for consistency
   r - get repairs
   m - get repaired models""")
    parser.add_argument("--exhaustive-search", action="store_true",
                        help="Force exhaustive search of function repair operations (default=false).")
    parser.add_argument("--sub-opt", action="store_true",
                        help="Show sub-optimal solutions found (default=false).")
    parser.add_argument("--all-opt", action="store_true",
                        help="""Computes all optimal solutions (default=true).
Stops at first optimal solution if false.""")
    parser.add_argument("-v", "--verbose", type=int, choices=[0, 1, 2], default=2,
                        help="""Specify output verbose level (default=2):
    0 - compact format
    1 - json format
    2 - human-readable format""")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")

    args = parser.parse_args()

    # Apply arguments to config and network
    network.input_file_network = args.model
    config.task = args.task
    config.force_optimum = args.exhaustive_search
    config.show_solution_for_each_inconsistency = args.sub_opt
    config.verbose = args.verbose
    config.debug = args.debug

    # Activate debug mode
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s: %(message)s')
    
    obs_args = args.observations
    if len(obs_args) % 2 != 0:
        parser.error("Expected an even number of arguments for -obs (pairs of obs_file and updater_name)")

    # Load updaters dynamically from updaters/ directory
    updaters = {}
    updater_dir = os.path.join(os.path.dirname(__file__), "updaters")
    for filename in os.listdir(updater_dir):
        if filename.endswith(".py") and filename not in ("__init__.py", "updater.py", "time_series_updater.py"):
            module_name = os.path.splitext(filename)[0]
            class_name = "".join(word.capitalize() for word in module_name.split("_"))
            file_path = os.path.join(updater_dir, filename)
            # Load module dynamically
            spec = util.spec_from_file_location(module_name, file_path)
            module = util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Get class from module
            updater_class = getattr(module, class_name)()
            # Add class to updaters dictionary
            updaters[module_name.replace('_','')] = updater_class

    for i in range(0, len(obs_args), 2):
        obs_path = obs_args[i]
        updater_name = obs_args[i+1]

        try:
            network.add_observation_file(obs_path)
            if updater_name not in updaters:
                raise Exception(f"Updater '{updater_name}' not found in updaters directory")
            network.add_updater(updaters[updater_name])
            if updater_name == 'steadystateupdater':
                network.has_ss_obs = True
            else:
                network.has_ts_obs = True
        except Exception as e:
            parser.error(str(e))

if __name__ == '__main__':
    network = Network()
    process_arguments(network)
    
    # Delegate parsing to the correct reader based on file extension
    try:
        parser = get_parser(network.input_file_network)
        parse = parser.read(network, network.input_file_network)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    if parse < 1 and not config.ignore_warnings:
        logger.error('Model definition with errors. Check documentation for input definition details.')
        sys.exit(1)

    # Check consistency
    f_inconsistencies, optimization = check_consistency(network)
    if config.task == 'c' or optimization == 0:
        print_consistency(f_inconsistencies, optimization)
        sys.exit(0)

    # Model revision
    repairs2apply = model_revision(network, f_inconsistencies, optimization)
    if config.task == 'm':
        import copy
        import itertools
        
        # 1. Collect all possible model combinations (Cartesian product of repair sets per solution)
        all_models_to_save = []
        for repair_sol in repairs2apply:
            nodes_with_repairs = []
            # Sort node IDs for deterministic output order
            for node_id in sorted(repair_sol.inconsistent_nodes.keys()):
                i_node = repair_sol.inconsistent_nodes[node_id]
                if i_node.repair_sets:
                    node_options = [(node_id, rs) for rs in i_node.repair_sets]
                    nodes_with_repairs.append(node_options)
            
            # Cartesian product of options across all nodes for THIS solution
            for combination in itertools.product(*nodes_with_repairs):
                node_repair_map = dict(combination)
                all_models_to_save.append((repair_sol, node_repair_map))

        # 2. Apply repairs and write files
        total_models = len(all_models_to_save)
        if total_models == 0:
            logger.info("No repaired models to generate.")
        else:
            padding = len(str(total_models))
            prefix, ext = os.path.splitext(network.input_file_network)
            for i, (repair_sol, node_repair_map) in enumerate(all_models_to_save):
                newNetwork = copy.deepcopy(network)
                apply_repair(newNetwork, repair_sol, node_repair_map)
                filename = f"{prefix}_{str(i+1).zfill(padding)}{ext}"
                parser.write(newNetwork, filename)
                print(f"Generated repaired model: {filename}")
