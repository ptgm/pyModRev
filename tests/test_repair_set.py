import pytest
from network.repair_set import RepairSet
from network.function import Function
from network.edge import Edge
from network.node import Node

@pytest.fixture
def repair_set():
    return RepairSet()

@pytest.fixture
def sample_data():
    n1, n2 = Node('node1'), Node('node2')
    f1 = Function('node1')
    e1 = Edge(n1, n2, 1)
    e2 = Edge(n2, n1, 0)
    return n1, n2, f1, e1, e2

def test_initial_values(repair_set):
    assert len(repair_set.repaired_functions) == 0
    assert len(repair_set.flipped_edges) == 0
    assert repair_set.n_repair_operations == 0

def test_add_repaired_function(repair_set, sample_data):
    _, _, f1, _, _ = sample_data
    repair_set.add_repaired_function(f1)
    assert f1 in repair_set.repaired_functions
    assert repair_set.n_repair_operations == 1

def test_add_flipped_edge(repair_set, sample_data):
    _, _, _, e1, _ = sample_data
    repair_set.add_flipped_edge(e1)
    assert e1 in repair_set.flipped_edges
    assert repair_set.n_flip_edges_operations == 1

def test_remove_edge(repair_set, sample_data):
    _, _, _, e1, _ = sample_data
    repair_set.remove_edge(e1)
    assert e1 in repair_set.removed_edges
    assert repair_set.n_add_remove_operations == 1

def test_repair_set_equality(sample_data):
    n1, n2, f1, e1, e2 = sample_data
    rs1 = RepairSet()
    rs2 = RepairSet()
    
    rs1.add_repaired_function(f1)
    rs1.add_flipped_edge(e1)
    
    rs2.add_repaired_function(f1)
    rs2.add_flipped_edge(e1)
    
    assert rs1 == rs2
    
    rs2.add_edge(e2)
    assert rs1 != rs2
    assert rs1 != "not a repair set"
