import os
from pymodrev.parsers.network_parser import NetworkParser
from pymodrev.parsers.parser_asp import ASPParser
from pymodrev.parsers.parser_bnet import BnetParser
from pymodrev.parsers.parser_ginml import GINMLParser

def get_parser(filepath: str) -> NetworkParser:
    """
    Factory function to return the appropriate NetworkParser based on the
    file extension of the given filepath.
    
    Args:
        filepath: The path to the network model file.
        
    Returns:
        An instance of a subclass of NetworkParser.
        
    Raises:
        ValueError: If the file extension is unsupported.
    """
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    if ext == '.lp':
        return ASPParser()
    elif ext == '.bnet':
        return BnetParser()
    elif ext in ('.ginml', '.zginml'):
        return GINMLParser()
    else:
        raise ValueError(f"Unsupported model file extension: '{ext}'. Supported extensions are: .lp, .bnet, .ginml, .zginml")
