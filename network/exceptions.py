"""
This module defines custom exception classes for the pyModRev system.
"""

class PyModRevError(Exception):
    """Base class for exceptions in this module."""
    pass

class NetworkError(PyModRevError):
    """Exception raised for errors related to network structure."""
    pass

class EdgeNotFoundError(NetworkError):
    """Exception raised when an edge is not found in the network."""
    pass

class ParseError(PyModRevError):
    """Exception raised for errors during network or observation file parsing."""
    pass

class SolverError(PyModRevError):
    """Exception raised when the ASP solver encounters an error or impossibility."""
    pass

class ConfigurationError(PyModRevError):
    """Exception raised for invalid configurations or command-line arguments."""
    pass
