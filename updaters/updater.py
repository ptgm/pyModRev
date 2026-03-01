"""
This module contains the Updater class, which serves as an abstract base class
for applying update rules based on different update types. It provides utility
methods for consistency checks and loading appropriate update logic based on
the configuration.
"""

import sys
from abc import ABC, abstractmethod
from typing import List, Tuple
import clingo
import os
from network.network import Network
from network.function import Function
from network.inconsistency_solution import InconsistencySolution
from configuration import config

class Updater(ABC):
    """
    The Updater class is the base class for all update-related logic. It
    defines the structure for applying update rules, checking consistency, and
    selecting the correct updater based on the update type. This class should
    be extended to implement specific update types such as synchronous,
    asynchronous, or complete updates.
    """

    @staticmethod
    @abstractmethod
    def apply_update_rules(ctl: clingo.Control, updater) -> None:
        """
        Subclasses must implement this method to apply update rules based on
        the update type (e.g., synchronous, asynchronous, etc.).
        """

    @staticmethod
    @abstractmethod
    def is_func_consistent_with_label_with_profile(
            network: Network,
            labeling: InconsistencySolution,
            function: Function,
            profile: str) -> bool:
        """
        Evaluates whether the function's regulatory logic aligns with the
        expected dynamic behavior of the network. This implementation assumes a
        time series (i.e. multiple time points) and does not handle a
        steady-state scenario.
        """

    @staticmethod
    @abstractmethod
    def n_func_inconsistent_with_label_with_profile(
            network: Network,
            labeling: InconsistencySolution,
            function: Function,
            profile: str) -> int:
        """
        Checks the consistency of a function with a specific profile in a given
        labeling. It evaluates the function's clauses over time and returns the
        consistency status (consistent, single inconsistency, or double
        inconsistency) based on the profile.
        """

    @staticmethod
    def check_consistency(network: Network) -> Tuple[List, int]:
        """
        This method loads the necessary rules, including base rules and network
        observation files, and applies consistency checks to the network. It
        also handles the logic for checking the optimization based on the
        update type.
        """
        result = []
        optimization = -2
        try:
            def logger(warning_code, message):
                if config.debug:
                    print(warning_code, file=sys.stderr)
                    print(message, file=sys.stderr)
            ctl = clingo.Control(['--opt-mode=optN'], logger, 20)

            base_lp = os.path.join(os.path.dirname(__file__), '..', 'asp_rules', 'base.lp')
            ctl.load(base_lp)

            for updater in network.updaters:
                updater.apply_update_rules(ctl, updater)
            ctl.load(network.input_file_network)
            for obs_file in network.observation_files:
                ctl.load(obs_file)
            ctl.ground([('base', [])])
            with ctl.solve(yield_=True) as handle:
                if handle.get().satisfiable:
                    for model in handle:
                        if model and model.optimality_proven:
                            from asp_helper import ASPHelper
                            res, opt = ASPHelper.parse_cc_model(model)
                            result.append(res)
                            optimization = opt
                else:
                    optimization = -1
        except Exception as e:
            print(f'Failed to check consistency: {e}')
            sys.exit(-1)
        return result, optimization

    @staticmethod
    def is_clause_satisfiable(
            clause,
            network: Network,
            time_map,
            function: Function) -> bool:
        """
        Evaluates whether a clause is satisfiable given the network and current time mapping.
        """
        regulators = function.bitarray_to_regulators(clause)
        for var in regulators:
            edge = network.get_edge(var, function.node_id)
            if edge is not None:
                # The clause is unsatisfied if the edge sign contradicts the value in time_map.
                if (edge.sign > 0) == (time_map[var] == 0):
                    return False
            else:
                print(f"WARN: Missing edge from {var} to {function.node_id}")
                return False
        return True

