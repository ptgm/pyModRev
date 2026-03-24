import os
import zipfile
import xml.etree.ElementTree as ET
import logging
from network.network import Network
from parsers.network_parser import NetworkParser
from parsers.boolean_expression import (
    parse_and_minimise_expression,
    add_positive_autoregulation
)

logger = logging.getLogger(__name__)

class GINMLParser(NetworkParser):
    """
    Parser for GINsim XML formats (.ginml, .zginml).
    Reads Boolean logic from `<exp str="...">` elements found
    inside `<value val="1">` blocks, converting them into monotone
    non-degenerate functions via the shared Quine-McCluskey pipeline.
    Also writes networks back to .ginml or .zginml format.
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

    def _build_ginml_xml(self, network: Network) -> str:
        """
        Build the GINML XML string from a Network object.
        
        Generates XML matching the GINsim regulatory graph format with:
        - <gxl> root element
        - <graph> with nodes (including <value><exp> for expressions)
        - <edge> elements with sign attributes
        """
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<!DOCTYPE gxl SYSTEM "http://ginsim.org/GINML_2_2.dtd">')
        lines.append('<gxl xmlns:xlink="http://www.w3.org/1999/xlink">')

        # Build nodeorder from network node identifiers
        node_ids = list(network.nodes.keys())
        nodeorder = " ".join(node_ids)
        # Use a generic graph id
        lines.append(f'  <graph class="regulatory" id="regulatory_graph" nodeorder="{nodeorder}">')

        # Emit nodes
        for node_id, node in network.nodes.items():
            func = node.function
            is_input = node_id in network.regulators.get(node_id, []) and \
                        func.regulators == [node_id] and \
                        len(func.regulators_by_term) == 1

            if is_input and func.regulators == [node_id]:
                # Input node (self-loop only) — mark as input="true"
                lines.append(f'    <node id="{node_id}" maxvalue="1" input="true">')
                lines.append(f'    </node>')
            elif func.regulators_by_term:
                lines.append(f'    <node id="{node_id}" maxvalue="1">')
                # Build boolean expression from function terms
                expr_str = self._function_to_expression(network, node_id, func)
                lines.append(f'      <value val="1">')
                lines.append(f'        <exp str="{self._xml_escape(expr_str)}"/>')
                lines.append(f'      </value>')
                lines.append(f'    </node>')
            else:
                lines.append(f'    <node id="{node_id}" maxvalue="1">')
                lines.append(f'    </node>')

        # Emit edges
        for node_id, edge_list in network.graph.items():
            for edge in edge_list:
                start_id = edge.start_node.identifier
                end_id = edge.end_node.identifier
                sign_str = "negative" if edge.sign == 0 else "positive"
                edge_id = f"{start_id}:{end_id}"
                lines.append(
                    f'    <edge id="{edge_id}" from="{start_id}" '
                    f'to="{end_id}" minvalue="1" sign="{sign_str}">'
                )
                lines.append(f'    </edge>')

        lines.append('  </graph>')
        lines.append('</gxl>')
        lines.append('')

        return "\n".join(lines)

    @staticmethod
    def _function_to_expression(network: Network, node_id: str, func) -> str:
        """
        Convert a function's regulators_by_term into a boolean expression string.
        Terms are joined with ' | ', regulators within a term with ' & '.
        Negative edges are prefixed with '!'.
        """
        terms = []
        for term_id in sorted(func.regulators_by_term.keys()):
            regulators = func.regulators_by_term[term_id]
            reg_strs = []
            for reg in regulators:
                try:
                    edge = network.get_edge(reg, node_id)
                    prefix = "!" if edge.sign == 0 else ""
                except Exception:
                    prefix = ""
                reg_strs.append(f"{prefix}{reg}")
            terms.append(" & ".join(reg_strs))
        return " | ".join(terms)

    @staticmethod
    def _xml_escape(s: str) -> str:
        """Escape special XML characters in attribute values."""
        s = s.replace("&", "&amp;")
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        s = s.replace('"', "&quot;")
        return s

    def write(self, network: Network, filename: str) -> None:
        """
        Write the provided Network object to a .ginml or .zginml file.
        
        - If filename ends with .ginml: writes a standalone GINML XML file
        - If filename ends with .zginml: writes a zip containing
          GINsim-data/regulatoryGraph.ginml
        """
        ginml_content = self._build_ginml_xml(network)

        if filename.endswith(".zginml"):
            try:
                with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr(
                        "GINsim-data/regulatoryGraph.ginml",
                        ginml_content
                    )
            except IOError as exc:
                raise ValueError(
                    f"ERROR!\tCannot write to file {filename}"
                ) from exc
        elif filename.endswith(".ginml"):
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(ginml_content)
            except IOError as exc:
                raise ValueError(
                    f"ERROR!\tCannot write to file {filename}"
                ) from exc
        else:
            raise ValueError(
                f"ERROR! Unsupported file extension for output: {filename}"
            )
