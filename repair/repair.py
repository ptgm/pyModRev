"""
This module applies a valid repair to a network.
"""

import logging
from typing import List

from network.inconsistency_solution import InconsistencySolution
from network.network import Network
from repair.consistency import check_consistency
from repair.topology import repair_inconsistencies
from configuration import config

logger = logging.getLogger(__name__)

def apply_repair(network: Network, repair: InconsistencySolution) -> None:
    """
    This function applies a valid repair to a network.
    """
    for node_id, i_node in repair.inconsistent_nodes.items():
        if not i_node.repair_sets:
            continue

        # Pick the first repair set for this node (they are all equally optimal)
        repair_set = i_node.repair_sets[0]

        # 1. Add edges
        for edge in repair_set.added_edges:
            start_node = network.get_node(edge.start_node.identifier)
            end_node = network.get_node(edge.end_node.identifier)
            network.add_edge(start_node, end_node, edge.sign)

        # 2. Remove edges
        for edge in repair_set.removed_edges:
            start_node = network.get_node(edge.start_node.identifier)
            end_node = network.get_node(edge.end_node.identifier)
            network.remove_edge(start_node, end_node)

        # 3. Flip edges
        for edge in repair_set.flipped_edges:
            target_edge = network.get_edge(edge.start_node.identifier,
                                           edge.end_node.identifier)
            target_edge.flip_sign()

        # 4. Update functions
        for func in repair_set.repaired_functions:
            node = network.get_node(func.node_id)
            node.function = func