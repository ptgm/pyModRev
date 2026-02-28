import pytest
from network.node import Node
from network.function import Function

def test_node_initialization():
    node = Node('test_node')
    assert node.identifier == 'test_node'
    assert isinstance(node.function, Function)
    assert node.function.node_id == 'test_node'

def test_node_add_function():
    node = Node('test_node')
    func = Function('test_function')
    node.function = func
    assert node.function == func
    assert node.function.node_id == 'test_function'

def test_node_get_function():
    node = Node('test_node')
    assert node.function.node_id == 'test_node'
    func = Function('test_function')
    node.function = func
    assert node.function == func

def test_node_get_id():
    node = Node('test_node')
    assert node.identifier == 'test_node'
