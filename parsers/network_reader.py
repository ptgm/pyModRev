from abc import ABC, abstractmethod
from network.network import Network

class NetworkReader(ABC):
    """
    Abstract base class for reading network models into a Network object.
    Subclasses must implement the 'read' method for specific file formats.
    """
    @abstractmethod
    def read(self, network: Network, filepath: str) -> int:
        """
        Populate the provided Network object from the given filepath.
        
        Args:
            network: The Network object to populate.
            filepath: The path to the model file.
            
        Returns:
            int: 1 on success, -1 or -2 on failure/errors.
        """
        pass
