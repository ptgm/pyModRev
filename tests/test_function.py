import pytest
from pyfunctionhood.function import Function as PFHFunction
from pyfunctionhood.clause import Clause
from network.function import Function

def test_function_initialization():
    func = Function('node_1')
    assert func.node_id == 'node_1'
    assert func.get_distance_from_original() == 0
    assert not func.get_son_consistent()
    assert func.get_regulators() == []
    assert func.get_regulators_by_term() == {}

def test_add_regulator_to_term():
    func = Function('node_1')
    func.add_regulator_to_term(1, 'reg_1')
    assert 'reg_1' in func.get_regulators()
    assert 'reg_1' in func.get_regulators_by_term()[1]
    
    func.add_regulator_to_term(2, 'reg_2')
    assert 'reg_2' in func.get_regulators()
    assert 'reg_2' in func.get_regulators_by_term()[2]

    # Duplicate check
    func.add_regulator_to_term(1, 'reg_1')
    assert len(func.get_regulators_by_term()[1]) == 1
    assert len(func.get_regulators()) == 2

def test_function_equality_and_hash():
    f1 = Function("node1")
    f1.add_regulator_to_term(1, "A")
    f1.add_regulator_to_term(1, "B")
    
    f2 = Function("node1")
    f2.add_regulator_to_term(1, "A")
    f2.add_regulator_to_term(1, "B")

    f3 = Function("node1")
    f3.add_regulator_to_term(1, "A")

    assert f1 == f2
    assert f1 != f3
    assert hash(f1) == hash(f2)
    assert f1 != "not a function"

def test_empty_function_equality():
    f1 = Function("node1")
    f2 = Function("node2") # Different node, same empty logic
    f3 = Function("node1")
    
    # Empty functions of same node should be equal if logic is same
    assert f1 == f3
    # Actually the current implementation says if both empty -> True
    # Let's check if node_id matters for hash
    assert hash(f1) == hash(f3)
    # If node_id matters for hash but not for eq, it might violate invariant if we aren't careful
    # But currently __eq__ for empty returns True.
    assert f1 == f2

def test_function_string_rep():
    f = Function("node1")
    f.add_regulator_to_term(1, "A")
    f.add_regulator_to_term(1, "B")
    f.add_regulator_to_term(2, "C")
    assert f.print_function() == "(A && B) || (C)"

def test_pfh_integration():
    f = Function("node1")
    f.add_regulator_to_term(1, "A")
    f.create_pfh_function()
    assert isinstance(f.get_pfh_function(), PFHFunction)
    assert f.get_n_clauses() == 1
