from abc import ABC, abstractmethod
from network.network import Network

class NetworkParser(ABC):
    """
    Abstract base class for reading and writing network models.
    Subclasses must implement 'read' and 'write' for specific file formats.
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

    @abstractmethod
    def write(self, network: Network, filename: str) -> None:
        """
        Write the provided Network object to a file.
        
        Args:
            network: The Network object to write.
            filename: The path to the output file.
        """
        pass
