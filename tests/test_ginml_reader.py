import os
import pytest
from network.network import Network
from parsers.ginml_reader import GINMLReader

@pytest.fixture
def reader():
    return GINMLReader()

@pytest.fixture
def network():
    return Network()

def test_ginml_reader_example(reader, network):
    """
    Test parsing the ginsim_example_function.ginml file.
    Expectations:
      - Node A is input: gets positive auto-regulation (A regulates A with sign=1)
      - Node B expression is "A": B gets one term {1: ["A"]} and edge A->B sign=1
      - Node G2 exp is "A | !B": two terms {1: ["A"], 2: ["B"]} 
        and edges A->G2 (sign=1) and B->G2 (sign=0)
    """
    filepath = "ginsim_example_function.ginml"
    
    # Check if the file exists in the current working directory
    if not os.path.exists(filepath):
        pytest.skip(f"Test file {filepath} not found.")

    result = reader.read(network, filepath)
    assert result == 1

    # Check that nodes exist
    nodes = set(network.nodes.keys())
    assert nodes == {'A', 'B', 'G2'}

    # Verify Node A (input)
    func_A = network.get_node('A').function
    assert func_A.regulators == ['A']
    assert func_A.regulators_by_term == {1: ['A']}
    assert network.get_edge('A', 'A').sign == 1

    # Verify Node B (formula: A)
    func_B = network.get_node('B').function
    assert func_B.regulators == ['A']
    assert func_B.regulators_by_term == {1: ['A']}
    assert network.get_edge('A', 'B').sign == 1

    # Verify Node G2 (formula: A | !B)
    func_G2 = network.get_node('G2').function
    assert set(func_G2.regulators) == {'A', 'B'}
    terms = {frozenset(v) for v in func_G2.regulators_by_term.values()}
    # DNF for A | !B is essentially A or !B (two terms) 
    assert terms == {frozenset({'A'}), frozenset({'B'})}
    assert network.get_edge('A', 'G2').sign == 1
    assert network.get_edge('B', 'G2').sign == 0
