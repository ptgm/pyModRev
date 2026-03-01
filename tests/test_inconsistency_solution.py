import pytest
from network.inconsistency_solution import InconsistencySolution
from network.repair_set import RepairSet

@pytest.fixture
def solution():
    return InconsistencySolution()

def test_initial_values(solution):
    assert solution.inconsistent_nodes == {}
    assert solution.v_label == {}
    assert not solution.has_impossibility

def test_add_generalization(solution):
    solution.add_generalization("node1")
    assert "node1" in solution.inconsistent_nodes
    assert solution.get_i_node("node1").repair_type == 1

def test_add_v_label(solution):
    solution.add_v_label("profile1", "node1", "value1", "time1")
    assert solution.v_label["profile1"]["time1"]["node1"] == "value1"

def test_compare_repairs(solution):
    sol2 = InconsistencySolution()
    sol2.n_ar_operations = 5
    solution.n_ar_operations = 3
    assert solution.compare_repairs(sol2) == 1

def test_add_repair_set(solution):
    rs = RepairSet()
    rs.n_add_remove_operations = 2
    rs.n_repair_operations = 2
    solution.add_generalization("node1")
    solution.add_repair_set("node1", rs)
    assert solution.n_ar_operations == 2
    assert solution.n_repair_operations == 2
