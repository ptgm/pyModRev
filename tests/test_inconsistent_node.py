import pytest
from network.inconsistent_node import InconsistentNode
from network.repair_set import RepairSet

@pytest.fixture
def nodes():
    return InconsistentNode('node1', True), InconsistentNode('node2', False)

def test_initial_values(nodes):
    n1, n2 = nodes
    assert n1.identifier == 'node1'
    assert n1.generalization
    assert not n2.generalization
    assert not n1.is_repaired()

def test_set_repair_type(nodes):
    n1, _ = nodes
    n1.repair_type = 3
    assert n1.repair_type == 3

def test_add_repair_set(nodes):
    n1, _ = nodes
    rs1 = RepairSet()
    rs1.n_repair_operations = 5
    n1.add_repair_set(rs1)
    assert n1.is_repaired()
    assert n1.n_repair_operations == 5
    
    # Better repair set
    rs2 = RepairSet()
    rs2.n_repair_operations = 3
    n1.add_repair_set(rs2)
    assert n1.n_repair_operations == 3
    assert len(n1.repair_sets) == 1

def test_topological_error(nodes):
    n1, _ = nodes
    n1.topological_error = True
    assert n1.has_topological_error()
