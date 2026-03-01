"""
This module provides the ASPHelper class, which contains utility methods for
working with Answer Set Programming (ASP) in network analysis.
It includes methods for validating input names, parsing network files,
checking consistency, and parsing ASP models to extract inconsistencies.
"""

from typing import List, Tuple
import clingo
import logging

from network.network import Network
from network.inconsistency_solution import InconsistencySolution
from updaters.updater import Updater

logger = logging.getLogger(__name__)

class ASPHelper:
    """
    A utility class for handling ASP-related tasks in network analysis.
    Provides methods for validating input names, parsing network files,
    checking consistency, and parsing ASP models.
    """

    @staticmethod
    def check_consistency(network: Network) -> Tuple[List[InconsistencySolution], int]:
        """
        Checks the consistency of the network based on the specified update
        type.
        """
        result = []
        optimization = -2
        result, optimization = Updater.check_consistency(network)
        return result, optimization

    @staticmethod
    def parse_cc_model(model: clingo.Model) -> Tuple[InconsistencySolution, int]:
        """
        Parses a clingo model to extract inconsistency information.
        """
        inconsistency = InconsistencySolution()
        count = 0
        for atom in model.symbols(atoms=True):
            name = atom.name
            args = atom.arguments
            if name == 'vlabel':
                if len(args) > 3:
                    inconsistency.add_v_label(str(args[0]), str(args[2]),
                                              int(str(args[3])),
                                              int(str(args[1])))
                else:
                    inconsistency.add_v_label(str(args[0]), str(args[1]),
                                              int(str(args[2])), 0)
                continue
            if name == 'r_gen':
                inconsistency.add_generalization(str(args[0]))
                continue
            if name == 'r_part':
                inconsistency.add_particularization(str(args[0]))
                continue
            if name == 'repair':
                count += 1
                continue
            if name == 'update':
                inconsistency.add_update(int(str(args[1])), str(args[0]),
                                         str(args[2]))
                continue
            if name == 'topologicalerror':
                inconsistency.add_topological_error(str(args[0]))
                continue
            if name == 'inc':
                inconsistency.add_inconsistent_profile(str(args[0]),
                                                       str(args[1]))
                continue
            if name == 'incT':
                inconsistency.add_inconsistent_profile(str(args[0]),
                                                       str(args[2]))
                inconsistency.add_inconsistent_profile(str(args[1]),
                                                       str(args[2]))
                continue
        return inconsistency, count
