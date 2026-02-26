"""
This script analyzes a given network model to determine its consistency.
If inconsistencies are found, it attempts to compute the minimal set of repair
operations needed to restore consistency.
"""

import sys
import os
import inspect
import logging

from importlib import util
from typing import List, Dict
from network.network import Network
from asp_helper import ASPHelper
from configuration import config
from updaters.async_updater import AsyncUpdater
from updaters.sync_updater import SyncUpdater
from updaters.steady_state_updater import SteadyStateUpdater
from updaters.complete_updater import CompleteUpdater
from repair.engine import model_revision

# Configure logger
logger = logging.getLogger(__name__)


def print_help() -> None:
    """
    Print help.
    """
    help_text = f"""
    Model Revision program.
      Given a model and a set of observations, it determines if the model is consistent.
      If not, it computes all the minimum number of repair operations in order to render the model consistent.
    Version: {config.version}
    Usage:
      main.py --model <model_file> --observations <obs_1> <updater_1> [<obs_2> <updater_2> ...] [options]

        --model,-m <model_file>             Input model file.
        --observations, -obs <obs/updater pairs...>  
                                            List of observation file and updater pairs.
                                            Each observation must be followed by its updater type.
                                              Example: -obs obs1.lp asyncupdater obs2.lp syncupdater
      options:
        --check-consistency,-cc             Check the consistency of the model and return without repairing. DEFAULT: false.
        --exhaustive-search                 Force exhaustive search of function repair operations. DEFAULT: false.
        --support,-su                       Support values for each variable.
        --sub-opt                           Show sub-optimal solutions found. DEFAULT: false.
        --verbose,-v <value>                Verbose level {{0,1,2,3}} of output. DEFAULT: 2.
                                              0 - machine style output (minimalistic easily parsable)
                                              1 - machine style output (using sets of sets)
                                              2 - human readable output
                                              3 - JSON format output
        --help,-h                           Print help options.
    """
    print(help_text)


def process_arguments(
        network: Network,
        argv: List[str]) -> None:
    """
    Process command-line arguments and configure network accordingly.
    """
    if len(argv) < 2:
        print_help()
        raise ValueError('Invalid number of arguments')

    # obs_type = 0
    last_opt = '-m'
    option_mapping = {
        '--sub-opt': 'show_solution_for_each_inconsistency',
        '--exhaustive-search': 'force_optimum',
        '--check-consistency': 'check_consistency',
        '-cc': 'check_consistency'
    }
    # retro_options = {'--steady-state', '--ss'}  # TODO delete
    help_options = {'--help', '-h'}
    model_options = {'--model', '-m'}
    observation_options = {'--observations', '-obs'}
    # observation_type_options = {'--observation-type', '-ot'}  # TODO delete
    # observation_type_values = {'ts': 0, 'ss': 1, 'both': 2}  # TODO delete
    # update_options = {'--update', '-up'}  # TODO delete
    # update_values = {'a': UpdateType.ASYNC, 's': UpdateType.SYNC, 'ma': UpdateType.MASYNC}  # TODO delete
    verbose_options = {'--verbose', '-v'}
    debug_options = {'--debug', '-d'}

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == 'main.py':
            i += 1
            continue
        if arg.startswith('-'):
            if arg in option_mapping:
                if arg == '--sub-opt': config.show_solution_for_each_inconsistency = True
                elif arg == '--exhaustive-search': config.force_optimum = True
                elif arg == '--check-consistency' or arg == '-cc': config.check_asp = True
            elif arg in model_options | \
                    observation_options | \
                    verbose_options:
                    # observation_type_options | \
                    # update_options | \
                last_opt = arg
            # elif arg in retro_options:
            #     obs_type = 1
            elif arg in help_options:
                print_help()
                sys.exit(0)
            elif arg in debug_options:
                config.debug = True
            else:
                print_help()
                raise ValueError(f'Invalid option: {arg}')
            i += 1
        else:
            if last_opt in model_options:
                if not network.get_input_file_network():
                    network.set_input_file_network(arg)
                i += 1
            elif last_opt in observation_options:
                while i < len(argv) and not argv[i].startswith('-'):
                    if i + 1 >= len(argv) or argv[i+1].startswith('-'):
                        print_help()
                        raise ValueError("Expected an updater name after the observation file path")
                    obs_path = argv[i]
                    network.add_observation_file(obs_path)
                    updater_name = argv[i + 1]
                    try:
                        if updater_name.lower() != SteadyStateUpdater.__name__.lower():
                            network.set_has_ts_obs(True)
                            if updater_name.lower() == SyncUpdater.__name__.lower():
                                network.add_updater_name('SyncUpdater')
                            elif updater_name.lower() == AsyncUpdater.__name__.lower():
                                network.add_updater_name('AsyncUpdater')
                            elif updater_name.lower() == CompleteUpdater.__name__.lower():
                                network.add_updater_name('CompleteUpdater')
                            else:
                                raise Exception("Unknown non-steady state updater type encountered")
                            if len(network.get_updaters_name()) > 1:
                                raise Exception(f"Conflicting updater types detected: {', '.join(network.get_updaters_name())} cannot coexist.")
                        else:
                            network.set_has_ss_obs(True)
                        updater_dir = os.path.join(os.path.dirname(__file__), "updaters")
                        for filename in os.listdir(updater_dir):
                            if filename.endswith(".py") and filename != os.path.basename(__file__):
                                file_path = os.path.join(updater_dir, filename)
                                classes = load_classes_from_file(file_path)
                                for name, cls in classes.items():
                                    if updater_name.lower() == name.lower():
                                        updater = cls()
                                        network.add_updater(updater)
                        i += 2
                    except ValueError as exc:
                        raise ValueError('Invalid updater') from exc
            # elif last_opt in observation_type_options:
            #     obs_type = observation_type_values.get(arg, None)
            #     if obs_type is None:
            #         print_help()
            #         raise ValueError(f'Invalid value for --observation-type: \
            #                          {arg}')
            #     i += 1
            # elif last_opt in update_options:
            #     config.update = update_values.get(arg, None)
            #     if config.update is None:
            #         print_help()
            #         raise ValueError(f'Invalid value for --update: {arg}')
            #     i += 1
            elif last_opt in verbose_options:
                try:
                    verbose_level = int(arg)
                    if 0 <= verbose_level <= 3:
                        config.verbose = verbose_level
                    else:
                        raise ValueError
                except ValueError as exc:
                    print_help()
                    raise ValueError(f'Invalid value for --verbose: {arg}') \
                        from exc
                i += 1
            else:
                i += 1


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
    process_arguments(network, sys.argv)
    parse = ASPHelper.parse_network(network)
    if parse < 1 and not config.ignore_warnings:
        logger.error('Model definition with errors. Check documentation for input definition details.')
        sys.exit(-1)
    model_revision(network)
