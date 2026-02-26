"""
This module contains the core engine for model revision and consistency checking.
"""

import math
from bitarray import bitarray
from typing import List, Dict, Tuple

from network.inconsistency_solution import InconsistencySolution
from network.inconsistent_node import InconsistentNode
from network.repair_set import RepairSet
from network.network import Network
from network.function import Function
from network.edge import Edge
from asp_helper import ASPHelper
from updaters.steady_state_updater import SteadyStateUpdater
from configuration import config, Inconsistencies

def repair_inconsistencies(
        network: Network,
        inconsistency: InconsistencySolution) -> None:
    """
    This function receives an inconsistent model with a set of nodes to be
    repaired and tries to repair the target nodes making the model consistent
    returning the set of repair operations to be applied.
    """
    for node_id, node in inconsistency.get_i_nodes().items():
        repair_node_consistency(network, inconsistency, node)
        if inconsistency.get_has_impossibility():
            if config.debug:
                print(f"#Found a node with impossibility - {node_id}")
            return
        if config.debug:
            print(f"#Found a repair for node - {node_id}")


def repair_node_consistency(
        network: Network,
        inconsistency: InconsistencySolution,
        inconsistent_node: InconsistentNode) -> None:
    """
    This function repairs a given node and determines all possible solutions
    consider 0 .. N add/remove repair operations, starting with 0 repairs of
    this type
    """
    original_node = network.get_node(inconsistent_node.get_id())
    original_function = original_node.get_function()
    original_regulators = original_function.get_regulators() \
        if original_function is not None \
        else []
    list_edges_remove = []
    list_edges_add = []

    for regulator in original_regulators:
        edge = network.get_edge(regulator, original_function.get_node_id())
        if edge is not None and not edge.get_fixed():
            list_edges_remove.append(edge)

    max_n_remove = len(list_edges_remove)
    max_n_add = len(network.get_nodes()) - max_n_remove

    for node_id, node in network.get_nodes().items():
        is_original_regulator = any(node_id == reg_id for reg_id in
                                    original_regulators)

        if not is_original_regulator:
            new_edge = Edge(node, original_node, 1)
            list_edges_add.append(new_edge)

    sol_found = False

    # Iterate through the number of add/remove operations
    for n_operations in range(max_n_remove + max_n_add + 1):
        for n_add in range(n_operations + 1):
            if n_add > max_n_add:
                break
            n_remove = n_operations - n_add
            if n_remove > max_n_remove:
                continue
            if config.debug:
                print(f"DEBUG: Testing {n_add} adds and {n_remove} removes")

            list_add_combination = get_edges_combinations(list_edges_add,
                                                          n_add)
            list_remove_combination = get_edges_combinations(list_edges_remove,
                                                             n_remove)

            for add_combination in list_add_combination:
                for remove_combination in list_remove_combination:
                    is_sol = False

                    # Remove and add edges
                    for edge in remove_combination:
                        if config.debug:
                            print(f"DEBUG: Remove edge from {edge.get_start_node().get_id()}")
                        network.remove_edge(edge.get_start_node(),
                                            edge.get_end_node())

                    for edge in add_combination:
                        if config.debug:
                            print(f"DEBUG: Add edge from {edge.get_start_node().get_id()}")
                        network.add_edge(edge.get_start_node(),
                                         edge.get_end_node(), edge.get_sign())

                    # If n_operations > 0, the function must be changed
                    if n_operations > 0:
                        new_function = Function(original_node.get_id())
                        clause_id = 1

                        for regulator in original_regulators:
                            removed = any(regulator ==
                                          edge.get_start_node().get_id()
                                          for edge in remove_combination)
                            if not removed:
                                # TODO try using add_regulator_to_term and only when needed add the clause
                                new_function.add_regulator_to_term(clause_id,
                                                                   regulator)
                                clause_id += 1

                        for edge in add_combination:
                            # TODO try using add_regulator_to_term and only when needed add the clause
                            new_function.add_regulator_to_term(
                                clause_id, edge.get_start_node().get_id())
                            clause_id += 1

                        # TODO does this makes sense? only creating the PFH function if the new function has regulators?
                        if new_function.get_regulators():
                            new_function.create_pfh_function()
                        original_node.add_function(new_function)

                    # Test with edge flips starting with 0 edge flips
                    is_sol = repair_node_consistency_flipping_edges(
                        network, inconsistency, inconsistent_node,
                        add_combination, remove_combination)

                    # Add and remove edges for the original network
                    for edge in remove_combination:
                        network.add_edge(edge.get_start_node(),
                                         edge.get_end_node(), edge.get_sign())

                    for edge in add_combination:
                        network.remove_edge(edge.get_start_node(),
                                            edge.get_end_node())

                    # Restore the original function
                    original_node.add_function(original_function)

                    if is_sol:
                        sol_found = True
                        if not config.all_opt:
                            if config.debug:
                                print("DEBUG: No more solutions - all_opt")
                            return
        if sol_found:
            break
    if not sol_found:
        inconsistency.set_impossibility(True)
        print(f"WARN: Not possible to repair node {inconsistent_node.get_id()}")
    return


def repair_node_consistency_flipping_edges(
        network: Network,
        inconsistency: InconsistencySolution,
        inconsistent_node: InconsistentNode,
        added_edges: List[Edge],
        removed_edges: List[Edge]) -> bool:
    """
    Tries to repair a node's consistency by flipping edges in the network.
    It tests different combinations of edge flips and checks if the
    inconsistency is resolved.
    """
    function = network.get_node(inconsistent_node.get_id()).get_function()
    regulators = function.get_regulators() if function is not None else []
    list_edges = []

    for regulator in regulators:
        edge = network.get_edge(regulator, function.get_node_id())
        if edge is not None and not edge.get_fixed():
            list_edges.append(edge)
    if config.debug:
        print(f"DEBUG: Searching solution flipping edges for {inconsistent_node.get_id()}")

    sol_found = False
    iterations = len(list_edges)

    # Limit the number of flip edges if the node has already been repaired
    if inconsistent_node.is_repaired():
        iterations = inconsistent_node.get_n_flip_edges_operations()
    for n_edges in range(iterations + 1):
        if config.debug:
            print(f"DEBUG: Testing with {n_edges} edge flips")

        edges_candidates = get_edges_combinations(list_edges, n_edges)

        # For each set of flipping edges
        for edge_set in edges_candidates:
            # Flip all edges
            for edge in edge_set:
                edge.flip_sign()
                if config.debug:
                    print(f"DEBUG: Flip edge from {edge.get_start_node().get_id()}")
            is_sol = repair_node_consistency_functions(network, inconsistency,
                                                       inconsistent_node,
                                                       edge_set, added_edges,
                                                       removed_edges)
            # Put network back to normal by flipping edges back
            for edge in edge_set:
                edge.flip_sign()
                if config.debug:
                    print(f"DEBUG: Return flip edge from {edge.get_start_node().get_id()}")
            if is_sol:
                if config.debug:
                    print("DEBUG: Is solution by flipping edges")
                sol_found = True
                if not config.all_opt:
                    if config.debug:
                        print("DEBUG: No more solutions - all_opt")
                    return True
        if sol_found:
            if config.debug:
                print(f"DEBUG: Ready to end with {n_edges} edges flipped")
            break

    return sol_found


def get_edges_combinations(
        edges: List[Edge],
        n: int,
        index_start: int = 0) -> List[List[Edge]]:
    """
    Generate all possible combinations of edges with specified size.
    """
    if n == 0:
        return [[]]
    result = []
    for i in range(index_start, len(edges) - n + 1):
        if n > 1:
            aux = get_edges_combinations(edges, n - 1, i + 1)
            for combination in aux:
                combination.append(edges[i])
                result.append(combination)
        else:
            result.append([edges[i]])
    return result


def repair_node_consistency_functions(
        network: Network,
        inconsistency: InconsistencySolution,
        inconsistent_node: InconsistentNode,
        flipped_edges: List[Edge],
        added_edges: List[Edge],
        removed_edges: List[Edge]) -> bool:
    """
    Repairs a node's function if needed by checking for consistency after
    topological changes, and if necessary, searches for a function change to
    resolve inconsistencies.
    """
    sol_found = False
    repair_type = inconsistent_node.get_repair_type()

    # If any topological operation was performed, validate if the model
    # became consistent
    if flipped_edges or added_edges or removed_edges:
        repair_type = n_func_inconsistent_with_label(
            network, inconsistency,
            network.get_node(inconsistent_node.get_id()).get_function())
        if repair_type == Inconsistencies.CONSISTENT.value:
            if config.debug:
                print("DEBUG: Node consistent with only topological changes")

            repair_set = RepairSet()

            for edge in flipped_edges:
                repair_set.add_flipped_edge(edge)

            # Add and remove edges in the solution repair set
            for edge in removed_edges:
                repair_set.remove_edge(edge)

            for edge in added_edges:
                repair_set.add_edge(edge)

            if added_edges or removed_edges:
                repair_set.add_repaired_function(network.get_node(
                    inconsistent_node.get_id()).get_function())

            inconsistency.add_repair_set(inconsistent_node.get_id(),
                                         repair_set)
            return True
    else:
        # No operation was performed yet, validate if it is a topological
        # change
        if inconsistent_node.has_topological_error():
            return False

    if repair_type == Inconsistencies.CONSISTENT.value:
        print(f"WARN: Found a consistent node before expected: {inconsistent_node.get_id()}")

    # If a solution was already found, avoid searching for function changes
    if inconsistent_node.is_repaired():
        n_ra_op = inconsistent_node.get_n_add_remove_operations()
        n_fe_op = inconsistent_node.get_n_flip_edges_operations()
        n_op = inconsistent_node.get_n_repair_operations()

        if (n_ra_op == len(added_edges) + len(removed_edges)) and (
                n_fe_op == len(flipped_edges)) and (n_op == n_ra_op + n_fe_op):
            if config.debug:
                print("DEBUG: Better solution already found. No function search.")
            return False

    # Model is not consistent and a function change is necessary
    if repair_type == Inconsistencies.DOUBLE_INC.value:
        if added_edges or removed_edges:
            # If we have a double inconsistency and at least one edge was
            # removed or added, it means that the function was changed to the
            # bottom function, and it's not repairable
            return False

        if config.debug:
            print(f"DEBUG: Searching for non-comparable functions for node {inconsistent_node.get_id()}")

        # Case of double inconsistency
        sol_found = search_non_comparable_functions(network, inconsistency,
                                                    inconsistent_node,
                                                    flipped_edges, added_edges,
                                                    removed_edges)

        if config.debug:
            print(f"DEBUG: End searching for non-comparable functions for node {inconsistent_node.get_id()}")

    else:
        if config.debug:
            print(f"DEBUG: Searching for comparable functions for node {inconsistent_node.get_id()}")

        # Case of single inconsistency
        sol_found = search_comparable_functions(
            network, inconsistency, inconsistent_node, flipped_edges,
            added_edges, removed_edges,
            repair_type == Inconsistencies.SINGLE_INC_GEN.value)
        if config.debug:
            print(f"DEBUG: End searching for comparable functions for node {inconsistent_node.get_id()}")

    return sol_found


def n_func_inconsistent_with_label(
        network: Network,
        labeling: InconsistencySolution,
        function: Function) -> int:
    """
    Checks the consistency of a function against a labeling. It verifies each
    profile and returns the consistency status (consistent, inconsistent, or
    double inconsistency).
    """
    result = Inconsistencies.CONSISTENT.value
    for key in labeling.get_v_label():
        ret = n_func_inconsistent_with_label_with_profile(network, labeling, function, key)
        if config.debug:
            print(f"DEBUG: Consistency value: {ret} for node {function.get_node_id()} with function: {function.print_function()}")
        if result == Inconsistencies.CONSISTENT.value:
            result = ret
        else:
            if ret not in (result, Inconsistencies.CONSISTENT.value):
                result = Inconsistencies.DOUBLE_INC.value
                break
    return result


def n_func_inconsistent_with_label_with_profile(
        network: Network,
        labeling: InconsistencySolution,
        function: Function,
        profile: str) -> int:
    """
    Checks the consistency of a function with a specific profile in a given
    labeling. It evaluates the function's clauses over time and returns the
    consistency status (consistent, single inconsistency, or double
    inconsistency) based on the profile.
    """
    if len(labeling.get_v_label()[profile]) == 1 and network.get_has_ss_obs():
        return SteadyStateUpdater.n_func_inconsistent_with_label_with_profile(network, labeling, function, profile)
    for updater in network.get_updaters():
        if len(labeling.get_v_label()[profile]) != 1 and updater.__class__.__name__.lower() != SteadyStateUpdater.__name__.lower():
            return updater.n_func_inconsistent_with_label_with_profile(network, labeling, function, profile)


def search_comparable_functions(
        network: Network,
        inconsistency: InconsistencySolution,
        inconsistent_node: InconsistentNode,
        flipped_edges: List[Edge],
        added_edges: List[Edge],
        removed_edges: List[Edge],
        generalize: bool) -> bool:
    """
    Searches for comparable functions that can repair the inconsistency of a
    node. It evaluates potential replacement functions and applies the
    necessary edges to resolve the inconsistency.
    """
    sol_found = False
    original_f = network.get_node(inconsistent_node.get_id()).get_function()

    if original_f is None:
        print(f"WARN: Inconsistent node {inconsistent_node.get_id()} without regulatory function")
        inconsistency.set_impossibility(True)
        return False

    if original_f.get_n_regulators() < 2:
        return False

    if config.debug:
        print(f"\tDEBUG: Searching for comparable functions of dimension {original_f.get_n_regulators()} going {'down' if generalize else 'up'}")

    # Get the replacement candidates
    function_repaired = False
    repaired_function_level = -1
    t_candidates = original_f.pfh_get_replacements(generalize)

    while t_candidates:
        candidate_sol = False
        candidate = t_candidates.pop(0)
        if function_repaired and candidate.get_distance_from_original() > \
                repaired_function_level:
            continue
        if is_func_consistent_with_label(network, inconsistency, candidate):
            candidate_sol = True
            repair_set = RepairSet()
            repair_set.add_repaired_function(candidate)
            for edge in flipped_edges:
                repair_set.add_flipped_edge(edge)
            for edge in removed_edges:
                repair_set.remove_edge(edge)
            for edge in added_edges:
                repair_set.add_edge(edge)
            inconsistency.add_repair_set(inconsistent_node.get_id(),
                                         repair_set)
            function_repaired = True
            sol_found = True
            repaired_function_level = candidate.get_distance_from_original()

            if not config.show_all_functions:
                break

        taux_candidates = candidate.pfh_get_replacements(generalize)
        if taux_candidates:
            for taux_candidate in taux_candidates:
                if not is_in(taux_candidate, t_candidates):
                    t_candidates.append(taux_candidate)

        if not candidate_sol:
            del candidate
    if not sol_found and config.force_optimum:
        return search_non_comparable_functions(network, inconsistency,
                                               inconsistent_node,
                                               flipped_edges, added_edges,
                                               removed_edges)
    return sol_found


def search_non_comparable_functions(
        network: Network,
        inconsistency: InconsistencySolution,
        inconsistent_node: InconsistentNode,
        flipped_edges: List[Edge],
        added_edges: List[Edge],
        removed_edges: List[Edge]) -> bool:
    """
    Searches for non-comparable functions to resolve inconsistencies in the
    given network. Attempts to replace an inconsistent function with a
    consistent alternative.
    """
    sol_found, function_repaired = False, False
    candidates, consistent_functions = [], []
    best_below, best_above, equal_level = [], [], []
    level_compare = config.compare_level_function

    # Each function must have a list of replacement candidates and each must
    # be tested until it works
    original_f = network.get_node(inconsistent_node.get_id()).get_function()
    original_map = original_f.get_regulators_by_term()

    if original_f.get_n_regulators() < 2:
        return False

    if config.debug:
        print(f"\tDEBUG: Searching for non-comparable functions of dimension {original_f.get_n_regulators()}")

    # Construction of new function to start search
    # TODO is missing the copy of the other attributes, might lead to error
    new_f = Function(original_f.get_node_id())

    # If the function is in the lower half of the Hasse diagram, start search
    # at the most specific function and generalize
    is_generalize = True
    if level_compare:
        if config.debug:
            print("DEBUG: Starting half determination")
        is_generalize = is_function_in_bottom_half(network, original_f)
        if config.debug:
            print("DEBUG: End half determination")
            print(f"DEBUG: Performing a search going {'up' if is_generalize else 'down'}")

    cindex = 1
    for _, _vars in original_map.items():
        for var in _vars:
            new_f.add_regulator_to_term(cindex, var)
            if not is_generalize:
                cindex += 1

    candidates.append(new_f)

    if config.debug:
        print(f"DEBUG: Finding functions for double inconsistency in {original_f.print_function()}")

    counter = 0
    while candidates:
        counter += 1
        candidate = candidates.pop(0)
        is_consistent = False

        if is_in(candidate, consistent_functions):
            continue

        inc_type = n_func_inconsistent_with_label(network, inconsistency,
                                                  candidate)
        if inc_type == Inconsistencies.CONSISTENT.value:
            is_consistent = True
            consistent_functions.append(candidate)
            if not function_repaired and config.debug:
                print(f"\tDEBUG: Found first function at level {candidate.get_distance_from_original()} {candidate.print_function()}")
            function_repaired, sol_found = True, True
            if level_compare:
                cmp = original_f.compare_level(candidate)
                if cmp == 0:
                    equal_level.append(candidate)
                    continue
                if (is_generalize and cmp < 0 and equal_level) \
                        or (not is_generalize and cmp > 0 and equal_level):
                    continue
                if cmp > 0 and not equal_level:
                    if not best_below:
                        best_below.append(candidate)
                    else:
                        rep_cmp = best_below[0].compare_level(candidate)
                        if rep_cmp == 0:
                            best_below.append(candidate)
                        elif rep_cmp < 0:
                            best_below = [candidate]
                    if not is_generalize:
                        continue
                if cmp < 0 and not equal_level:
                    if not best_above:
                        best_above.append(candidate)
                    else:
                        rep_cmp = best_above[0].compare_level(candidate)
                        if rep_cmp == 0:
                            best_above.append(candidate)
                        elif rep_cmp > 0:
                            best_above = [candidate]
                    if is_generalize:
                        continue
        else:
            if candidate.son_consistent:
                del candidate
                continue

            if inc_type == Inconsistencies.DOUBLE_INC.value or \
                    (is_generalize
                     and inc_type == Inconsistencies.SINGLE_INC_PART.value) \
                    or (not is_generalize
                        and inc_type == Inconsistencies.SINGLE_INC_GEN.value):
                del candidate
                continue

            if level_compare:
                if is_generalize and equal_level \
                        and candidate.compare_level(original_f) > 0:
                    del candidate
                    continue
                if not is_generalize and equal_level \
                        and candidate.compare_level(original_f) < 0:
                    del candidate
                    continue
                if is_generalize and best_above:
                    if best_above[0].compare_level(candidate) < 0:
                        del candidate
                        continue
                if not is_generalize and best_below:
                    if best_below[0].compare_level(candidate) > 0:
                        del candidate
                        continue

        new_candidates = candidate.get_replacements(is_generalize)
        for new_candidate in new_candidates:
            new_candidate.set_son_consistent(is_consistent)
            if not is_in(new_candidate, candidates):
                candidates.append(new_candidate)
        if not is_consistent:
            del candidate

    if config.debug:
        if function_repaired:
            if level_compare:
                print("\nDEBUG: Printing consistent functions found using level comparison")
                if equal_level:
                    print(f"Looked at {counter} functions. Found {len(consistent_functions)} consistent. Returning {len(equal_level)} functions of same level\n")
                else:
                    print(f"Looked at {counter} functions. Found {len(consistent_functions)} consistent. Returning {len(best_below) + len(best_above)} functions\n")
            else:
                print(f"DEBUG: Looked at {counter} functions. Found {len(consistent_functions)} functions\n")
        else:
            print(f"DEBUG: No consistent functions found - {counter}")

    # Add repair sets to the solution
    if sol_found:
        if level_compare:
            for candidate_set in (equal_level if equal_level else best_below +
                                  best_above):
                repair_set = RepairSet()
                repair_set.add_repaired_function(candidate_set)
                for edge in flipped_edges:
                    repair_set.add_flipped_edge(edge)
                for edge in removed_edges:
                    repair_set.remove_edge(edge)
                for edge in added_edges:
                    repair_set.add_edge(edge)
                inconsistency.add_repair_set(inconsistent_node.get_id(),
                                             repair_set)
        else:
            for candidate in consistent_functions:
                repair_set = RepairSet()
                repair_set.add_repaired_function(candidate)
                for edge in flipped_edges:
                    repair_set.add_flipped_edge(edge)
                for edge in removed_edges:
                    repair_set.remove_edge(edge)
                for edge in added_edges:
                    repair_set.add_edge(edge)
                inconsistency.add_repair_set(inconsistent_node.get_id(),
                                             repair_set)
    return sol_found


def is_function_in_bottom_half(
        network: Network,
        function: Function) -> bool:
    """
    Determines if a function is in the bottom half based on its regulators.
    If exact middle determination is enabled, it uses a different method.
    """
    if config.exact_middle_function_determination:
        if config.debug:
            print("DEBUG: Half determination by state")
        return is_function_in_bottom_half_by_state(network, function)
    n = function.get_n_regulators()
    n2 = n // 2
    mid_level = [n2 for _ in range(n)]
    return function.compare_level_list(mid_level) < 0


def is_function_in_bottom_half_by_state(
        network: Network,
        function: Function) -> bool:
    """
    Determines if a function is in the bottom half based on its state by
    evaluating its output across all possible input combinations.
    """
    regulators = function.get_regulators()
    n_regulators = function.get_n_regulators()
    entries = int(math.pow(2, n_regulators))
    n_one = 0
    n_zero = 0
    for entry in range(entries):
        # Use bitarray to simulate the bitset, little-endian order
        bits = bitarray(bin(entry)[2:].zfill(16)[::-1])
        input_map = {}
        bit_index = 0
        for regulator in regulators:
            input_map[regulator] = 1 if bits[bit_index] else 0
            bit_index += 1
        if get_function_value(network, function, input_map):
            n_one += 1
            if n_one > (entries // 2):
                break
        else:
            n_zero += 1
            if n_zero > (entries // 2):
                break
    return n_zero > (entries // 2)


def get_function_value(
        network: Network,
        function: Function,
        input_map: Dict[str, int]):
    """
    Evaluates the value of a function based on the given input map. It checks
    the satisfaction of the function's clauses.
    """
    n_clauses = function.get_n_clauses()
    if n_clauses:
        clauses = function.get_clauses()
        for clause in clauses:
            is_clause_satisfiable = True
            _vars = function.bitarray_to_regulators(clause)
            for var in _vars:
                edge = network.get_edge(var, function.get_node_id())
                if edge is not None:
                    # Determine if clause is satisfiable based on edge sign
                    if (edge.get_sign() > 0) == (input_map[var] == 0):
                        is_clause_satisfiable = False
                        # Stop checking if clause is already unsatisfiable
                        break
                else:
                    print(f"WARN: Missing edge from {var} to {function.get_node_id()}")
                    return False
            if is_clause_satisfiable:
                return True
    return False


def is_func_consistent_with_label(
        network: Network,
        labeling: InconsistencySolution,
        function: Function) -> bool:
    """
    Checks if a function is consistent with a labeling across all profiles.
    """
    return all(
        is_func_consistent_with_label_with_profile(network, labeling, function, profile)
        for profile in labeling.get_v_label()
    )


def is_func_consistent_with_label_with_profile(
        network: Network,
        labeling: InconsistencySolution,
        function: Function,
        profile: str) -> bool:
    """
    Evaluates whether the function's regulatory logic aligns with the expected
    time-dependent behavior of the network, ensuring that the function's
    clauses are satisfied at each time step. It considers both stable states
    and dynamic updates based on the profile's labeling.
    """
    if len(labeling.get_v_label()[profile]) == 1 and network.get_has_ss_obs():
        return SteadyStateUpdater.is_func_consistent_with_label_with_profile(network, labeling, function, profile)
    for updater in network.get_updaters():
        if len(labeling.get_v_label()[profile]) != 1 and updater.__class__.__name__.lower() != SteadyStateUpdater.__name__.lower():
            return updater.is_func_consistent_with_label_with_profile(network, labeling, function, profile)


def is_in(
        item: Function,
        lst: List[Function]) -> bool:
    """
    Checks if a function is present in a list by comparing it to each element.
    """
    return any(item.is_equal(aux) for aux in lst)


def check_consistency(network: Network) -> Tuple[List[InconsistencySolution], int]:
    """
    Check network consistency using ASP solver or alternative method.
    """
    result = []
    optimization = -2
    if config.check_asp:
        # result, optimization = ASPHelper.check_consistency(network, config.update.value)
        result, optimization = ASPHelper.check_consistency(network)
    else:
        pass
    return result, optimization


def model_revision(network: Network) -> None:
    """
    Analyze and revise a given network model for consistency.
    Procedure:
        1st - tries to repair functions
        2nd - tries to flip the sign of the edges
        3rd - tries to add or remove edges
    """
    optimization = -2
    f_inconsistencies, optimization = check_consistency(network)
    if config.check_consistency:
        print_consistency(f_inconsistencies, optimization)
        return

    if optimization < 0:
        print("ERROR: It is not possible to repair this network for now.")
        print("This may occur if there is at least one node for which from the same input two different outputs are expected (non-deterministic function).")
        return

    if optimization == 0:
        if config.verbose == 3:
            print_consistency(f_inconsistencies, optimization)
            return
        print("This network is consistent!")
        return

    if config.debug:
        print(f"Found {len(f_inconsistencies)} solution(s) with {len(f_inconsistencies[0].get_i_nodes())} inconsistent node(s)")

    # At this point we have an inconsistent network with node candidates
    # to be repaired
    best_solution = None
    for inconsistency in f_inconsistencies:
        repair_inconsistencies(network, inconsistency)

        # Check for valid solution
        if not inconsistency.get_has_impossibility():
            if best_solution is None \
                    or inconsistency.compare_repairs(best_solution) > 0:
                best_solution = inconsistency
                if config.debug:
                    print(f"DEBUG: Found a solution with {best_solution.get_n_topology_changes()} topology changes")
                if best_solution.get_n_topology_changes() == 0 and not \
                        config.all_opt:
                    break
        else:
            if config.debug:
                print("DEBUG: Reached an impossibility")

    if best_solution is None:
        print("### It was not possible to repair the model.")
        return

    show_sub_opt = config.show_solution_for_each_inconsistency

    if config.all_opt:
        for inconsistency in f_inconsistencies:
            if config.debug:
                print(f"DEBUG: Checking for printing solution with {inconsistency.get_n_topology_changes()} topology changes")
            if not inconsistency.get_has_impossibility() \
                    and (inconsistency.compare_repairs(best_solution) >= 0
                         or show_sub_opt):
                if show_sub_opt \
                        and inconsistency.compare_repairs(best_solution) < 0:
                    if config.verbose < 2:
                        print("+", end="")
                    else:
                        print("(Sub-Optimal Solution)")
                inconsistency.print_solution(config.verbose, True)
    else:
        best_solution.print_solution(config.verbose, True)


def print_consistency(
        inconsistencies: List[InconsistencySolution],
        optimization: int) -> None:
    """
    Print the consistency status of the network in a structured JSON-like
    format.
    """
    print("{")
    print(f'\t"consistent": {"true" if optimization == 0 else "false,"}')
    if optimization != 0:
        print('\t"inconsistencies": [', end="")
        for i, inconsistency in enumerate(inconsistencies):
            if i > 0:
                print(",", end="")
            print("\n\t\t{", end="")
            inconsistency.print_inconsistency("\t\t\t")
            print("\n\t\t}", end="")
        print("\n\t]")
    print("}")


