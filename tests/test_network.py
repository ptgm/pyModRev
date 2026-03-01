import pytest
from network.network import Network
from network.edge import Edge
from network.node import Node
from network.exceptions import EdgeNotFoundError

@pytest.fixture
def network():
    return Network()

def test_get_node(network):
    node = network.add_node('node_1')
    retrieved_node = network.get_node('node_1')
    assert retrieved_node == node
    assert network.get_node('non_existing_node') is None

def test_get_nodes(network):
    network.add_node('node_1')
    network.add_node('node_2')
    nodes = network.nodes
    assert len(nodes) == 2
    assert 'node_1' in nodes
    assert 'node_2' in nodes

def test_add_edge(network):
    node_1 = network.add_node('node_1')
    node_2 = network.add_node('node_2')
    network.add_edge(node_1, node_2, 1)
    
    edge = network.get_edge('node_1', 'node_2')
    assert edge.start_node == node_1
    assert edge.end_node == node_2
    assert 'node_1' in network.regulators['node_2']

def test_get_edge_not_found(network):
    network.add_node('node_1')
    with pytest.raises(EdgeNotFoundError):
        network.get_edge('node_1', 'node_2')

def test_remove_edge(network):
    node_1 = network.add_node('node_1')
    node_2 = network.add_node('node_2')
    network.add_edge(node_1, node_2, 1)
    network.remove_edge(node_1, node_2)
    
    with pytest.raises(EdgeNotFoundError):
        network.get_edge('node_1', 'node_2')
    assert 'node_2' not in network.regulators

def test_network_flags(network):
    network.has_ss_obs = True
    assert network.has_ss_obs
    network.has_ss_obs = False
    assert not network.has_ss_obs

    network.has_ts_obs = True
    assert network.has_ts_obs
    network.has_ts_obs = False
    assert not network.has_ts_obs

def test_observation_files(network):
    network.add_observation_file('obs1.lp')
    assert 'obs1.lp' in network.observation_files
