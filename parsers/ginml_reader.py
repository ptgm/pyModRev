import os
import zipfile
import xml.etree.ElementTree as ET
import logging
from network.network import Network
from parsers.network_reader import NetworkReader
from parsers.boolean_expression import (
    parse_and_minimise_expression,
    add_positive_autoregulation
)

logger = logging.getLogger(__name__)

class GINMLReader(NetworkReader):
    """
    Reader for GINsim XML formats (.ginml, .zginml).
    This reader parses Boolean logic from `<exp str="...">` elements found
    inside `<value val="1">` blocks, converting them into monotone
    non-degenerate functions via the shared Quine-McCluskey pipeline.
    
    It ignores arbitrary `<parameter>` tags and `<edge>` definitions,
    inferring the regulatory edges automatically from the formulas.
    """

    def read(self, network: Network, filepath: str) -> int:
        """
        Main entry point for reading a local .ginml or .zginml file.
        Returns 1 on success, -1 on soft warnings like unsupported parameters, 
        or raises ValueError / returns negative error codes for fatal failures.
        """
        if not os.path.exists(filepath):
            raise ValueError(f"ERROR! File {filepath} not found.")

        result = 1
        xml_content = None

        if filepath.endswith(".zginml"):
            try:
                with zipfile.ZipFile(filepath, 'r') as zf:
                    # GINsim zginml typically holds "GINsim-data/regulatoryGraph.ginml"
                    # But we can just search for the first .ginml file
                    ginml_file = None
                    for name in zf.namelist():
                        if name.endswith('.ginml'):
                            ginml_file = name
                            break
                    if not ginml_file:
                        logger.error(f"ERROR! No .ginml file found inside zip {filepath}")
                        return -1
                    xml_content = zf.read(ginml_file)
            except zipfile.BadZipFile:
                raise ValueError(f"ERROR! Invalid zip format for {filepath}")
        elif filepath.endswith(".ginml"):
            with open(filepath, 'rb') as f:
                xml_content = f.read()
        else:
            raise ValueError(f"ERROR! Unsupported file extension for {filepath}")

        # Parse XML
        try:
            tree = ET.ElementTree(ET.fromstring(xml_content))
            root = tree.getroot()
        except ET.ParseError as e:
            raise ValueError(f"ERROR! XML parsing failed in {filepath}: {e}")

        # Ensure we are reading a regulatory graph
        if root.tag != 'gxl':
            logger.warning("Root element is not gxl. Proceeding cautiously.")

        graph = root.find('.//graph')
        if graph is None:
            raise ValueError(f"ERROR! No <graph> element found in {filepath}")

        # 1. Parse Nodes
        for node_elem in graph.findall('node'):
            node_id = node_elem.get('id')
            if not node_id:
                continue

            maxvalue = node_elem.get('maxvalue', '1')
            try:
                if int(maxvalue) > 1:
                    logger.error(
                        f"PyModRev only supports Boolean networks! "
                        f"Node {node_id} has maxvalue={maxvalue}."
                    )
                    return -1
            except ValueError:
                pass # Default to boolean if parsing fails

            # Add node to network
            node_obj = network.add_node(node_id)

            # Check if node is an input node
            input_node = node_elem.get('input', 'false')
            if input_node.lower() == 'true':
                logger.info(f"Input: {node_obj.identifier}")
                add_positive_autoregulation(network, node_obj, node_id)
                continue

            # Look for boolean expression: <value val="1"><exp str="..."/></value>
            # or parameter logical parsing (which we skip now)
            value_elem = node_elem.find(".//value[@val='1']")
            if value_elem is not None:
                exp_elem = value_elem.find('exp')
                if exp_elem is not None:
                    expr_str = exp_elem.get('str')
                    if expr_str:
                        parse_result = parse_and_minimise_expression(
                            network, 
                            node_obj, 
                            node_id, 
                            expr_str,
                            location_info=f"in node {node_id}"
                        )
                        if parse_result < result:
                            result = parse_result

        # <edge> elements are completely ignored
        # edges and signs are detected via Quine-McCluskey minimisation

        return result
