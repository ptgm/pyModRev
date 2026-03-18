"""
BNet reader that delegates boolean expression parsing to the shared
boolean_expression module.
"""

import logging

from network.network import Network
from parsers.network_reader import NetworkReader
from parsers.boolean_expression import (
    parse_and_minimise_expression,
    add_positive_autoregulation
)

logger = logging.getLogger(__name__)


class BnetReader(NetworkReader):
    """
    Reads .bnet files and converts each boolean expression into a monotone
    non-degenerate form using Quine-McCluskey minimisation (via shared parser).
    """

    HEADER_TOKENS = {'targets', 'factors'}

    def read(self, network: Network, filepath: str) -> int:
        """
        Parse a .bnet file and populate the provided Network object.

        Returns:
            1 on success, -1 on warnings, -2 on fatal error.
        """
        result = 1

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                bnet_content = f.read()
        except IOError as exc:
            raise ValueError(f"ERROR!\tCannot open file {filepath}") from exc

        for count_line, raw_line in enumerate(bnet_content.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith('#'):
                continue
            if self._is_header_line(line):
                continue

            if ',' not in line:
                logger.warning(
                    f'WARN!\tLine {count_line} has no comma separator, '
                    f'skipping: {raw_line}'
                )
                result = -1
                continue

            target_str, expr_str = line.split(',', 1)
            target = target_str.strip()
            expr = expr_str.strip()

            if not target:
                logger.warning(
                    f'WARN!\tEmpty target name on line {count_line}: '
                    f'{raw_line}'
                )
                result = -1
                continue

            target_node = network.add_node(target)

            # Handle constant expressions
            if expr in ('0', '1'):
                logger.info(
                    f'Line {count_line}: target "{target}" has constant '
                    f'value {expr}, adding positive auto-regulation.'
                )
                add_positive_autoregulation(network, target_node, target)
                continue

            if not expr:
                logger.warning(
                    f'WARN!\tEmpty expression for target "{target}" on '
                    f'line {count_line}: {raw_line}'
                )
                result = -1
                continue

            # Parse, minimise, and populate using shared module
            parse_result = parse_and_minimise_expression(
                network, 
                target_node, 
                target, 
                expr,
                location_info=f"on line {count_line}"
            )
            
            if parse_result < result:
                result = parse_result
            if result == -2:
                return result

        return result

    @staticmethod
    def _is_header_line(line: str) -> bool:
        """Detect the optional bnet header line: 'targets, factors'."""
        parts = [p.strip().lower() for p in line.split(',')]
        return set(parts) == BnetReader.HEADER_TOKENS
