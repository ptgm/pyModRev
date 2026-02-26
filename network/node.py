"""
This module defines the Node class, which represents a node in a network.
A node has an identifier and an associated function, and provides methods to
manage these properties.
"""

from network.function import Function


class Node:
    """
    Represents a node in a network.
    A node has an identifier and an associated function, which can be managed
    using the provided methods.
    """
    def __init__(self, node_id: str) -> None:
        """
        Initializes a node with a given identifier and a default function.
        """
        self._identifier = node_id
        self._function = Function(node_id)

    @property
    def identifier(self) -> str:
        """Returns the identifier of the node."""
        return self._identifier

    @property
    def function(self) -> Function:
        """Returns the function associated with the node."""
        return self._function

    @function.setter
    def function(self, value: Function):
        """Sets the function associated with the node."""
        self._function = value

    def add_function(self, function: Function) -> None:
        """
        Sets or updates the function associated with the node.
        """
        self.function = function

    def get_function(self) -> Function:
        """
        Returns the function associated with the node.
        """
        return self.function

    def get_id(self) -> str:
        """
        Returns the identifier of the node.
        """
        return self.identifier
