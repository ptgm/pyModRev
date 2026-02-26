"""
This module defines the RepairSet class, which represents a set of repairs
for inconsistencies in a network.
The class provides methods to manage and analyze repaired functions, flipped
edges, removed edges, and added edges.
"""

from typing import List, Set, Dict, Any, TYPE_CHECKING
from network.edge import Edge
from network.function import Function

class RepairSet:
    """
    Represents a set of repairs for inconsistencies in a network.
    Provides methods to manage repaired functions, flipped edges, removed
    edges, and added edges.
    """
    def __init__(self):
        """
        Initializes an empty repair set with no repaired functions, edges, or
        operations.
        """
        self._repairs = {
            'repaired_functions': set(),
            'flipped_edges': set(),
            'removed_edges': set(),
            'added_edges': set()
        }
        self._stats = {
            'n_topology_changes': 0,
            'n_repair_operations': 0,
            'n_add_remove_operations': 0,
            'n_flip_edges_operations': 0
        }

    def get_repaired_functions(self) -> Set[Function]:
        """
        Returns the set of repaired functions in the repair set.
        """
        return self._repairs['repaired_functions']

    def get_flipped_edges(self) -> Set[Edge]:
        """
        Returns the set of flipped edges in the repair set.
        """
        return self._repairs['flipped_edges']

    def get_removed_edges(self) -> Set[Edge]:
        """
        Returns the set of removed edges in the repair set.
        """
        return self._repairs['removed_edges']

    def get_added_edges(self) -> Set[Edge]:
        """
        Returns the set of added edges in the repair set.
        """
        return self._repairs['added_edges']

    def get_n_topology_changes(self) -> int:
        """
        Returns the number of topology changes in the repair set.
        """
        return self._stats['n_topology_changes']

    def get_n_repair_operations(self) -> int:
        """
        Returns the total number of repair operations in the repair set.
        """
        return self._stats['n_repair_operations']

    def get_n_flip_edges_operations(self) -> int:
        """
        Returns the number of edge flip operations in the repair set.
        """
        return self._stats['n_flip_edges_operations']

    def get_n_add_remove_operations(self) -> int:
        """
        Returns the number of add/remove operations in the repair set.
        """
        return self._stats['n_add_remove_operations']

    def add_repaired_function(self, function: Function) -> None:
        """
        Adds a repaired function to the repair set and updates repair
        statistics.
        """
        if function not in self._repairs['repaired_functions']:
            self._repairs['repaired_functions'].add(function)
            self._stats['n_repair_operations'] += 1

    def add_flipped_edge(self, edge: Edge) -> None:
        """
        Adds a flipped edge to the repair set and updates repair statistics.
        """
        if edge not in self._repairs['flipped_edges']:
            self._repairs['flipped_edges'].add(edge)
            self._stats['n_repair_operations'] += 1
            self._stats['n_topology_changes'] += 1
            self._stats['n_flip_edges_operations'] += 1

    def remove_edge(self, edge: Edge) -> None:
        """
        Adds a removed edge to the repair set and updates repair statistics.
        """
        if edge not in self._repairs['removed_edges']:
            self._repairs['removed_edges'].add(edge)
            self._stats['n_repair_operations'] += 1
            self._stats['n_topology_changes'] += 1
            self._stats['n_add_remove_operations'] += 1

    def add_edge(self, edge: Edge) -> None:
        """
        Adds an added edge to the repair set and updates repair statistics.
        """
        if edge not in self._repairs['added_edges']:
            self._repairs['added_edges'].add(edge)
            self._stats['n_repair_operations'] += 1
            self._stats['n_topology_changes'] += 1
            self._stats['n_add_remove_operations'] += 1

    @property
    def repaired_functions(self) -> Set[Function]:
        return self._repairs['repaired_functions']

    @repaired_functions.setter
    def repaired_functions(self, value: Set[Function]):
        self._repairs['repaired_functions'] = set(value)

    @property
    def flipped_edges(self) -> Set[Edge]:
        return self._repairs['flipped_edges']

    @flipped_edges.setter
    def flipped_edges(self, value: Set[Edge]):
        self._repairs['flipped_edges'] = set(value)

    @property
    def removed_edges(self) -> Set[Edge]:
        return self._repairs['removed_edges']

    @removed_edges.setter
    def removed_edges(self, value: Set[Edge]):
        self._repairs['removed_edges'] = set(value)

    @property
    def added_edges(self) -> Set[Edge]:
        return self._repairs['added_edges']

    @added_edges.setter
    def added_edges(self, value: Set[Edge]):
        self._repairs['added_edges'] = set(value)

    @property
    def n_topology_changes(self) -> int:
        return self._stats['n_topology_changes']

    @n_topology_changes.setter
    def n_topology_changes(self, value: int):
        self._stats['n_topology_changes'] = value

    @property
    def n_repair_operations(self) -> int:
        return self._stats['n_repair_operations']

    @n_repair_operations.setter
    def n_repair_operations(self, value: int):
        self._stats['n_repair_operations'] = value

    @property
    def n_add_remove_operations(self) -> int:
        return self._stats['n_add_remove_operations']

    @n_add_remove_operations.setter
    def n_add_remove_operations(self, value: int):
        self._stats['n_add_remove_operations'] = value

    @property
    def n_flip_edges_operations(self) -> int:
        return self._stats['n_flip_edges_operations']

    @n_flip_edges_operations.setter
    def n_flip_edges_operations(self, value: int):
        self._stats['n_flip_edges_operations'] = value

    def is_equal(self, other: 'RepairSet') -> bool:
        """
        Checks if this repair set is equal to another repair set.
        """
        return (
            self.repaired_functions == other.repaired_functions and
            self.flipped_edges == other.flipped_edges and
            self.removed_edges == other.removed_edges and
            self.added_edges == other.added_edges
        )

