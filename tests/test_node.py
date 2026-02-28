import pytest
from network.node import Node
from network.function import Function

def test_node_initialization():
    node = Node('test_node')
    assert node.get_id() == 'test_node'
    assert isinstance(node.get_function(), Function)
    assert node.get_function().get_node_id() == 'test_node'

def test_node_add_function():
    node = Node('test_node')
    func = Function('test_function')
    node.add_function(func)
    assert node.get_function() == func
    assert node.get_function().get_node_id() == 'test_function'

def test_node_get_function():
    node = Node('test_node')
    assert node.get_function().get_node_id() == 'test_node'
    func = Function('test_function')
    node.add_function(func)
    assert node.get_function() == func

def test_node_get_id():
    node = Node('test_node')
    assert node.get_id() == 'test_node'
