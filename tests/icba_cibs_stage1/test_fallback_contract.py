"""Outcome-free proof tests for the Stage-I full-enumeration fallback."""

from __future__ import annotations

import heapq
import random
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "third_party/hnswlib/hnswlib/hnswalg.h"


def full_ef_search(graph, entry, distances, ef):
    """Small faithful model of hnswlib's bare-bone layer-0 loop."""
    visited = {entry}
    # Python heaps are min-heaps; candidates store nearest first.
    candidates = [(distances[entry], entry)]
    retained = [(-distances[entry], entry)]  # farthest distance at heap root
    while candidates:
        candidate_dist, node = candidates[0]
        lower_bound = -retained[0][0]
        if candidate_dist > lower_bound:
            break
        heapq.heappop(candidates)
        for neighbor in graph[node]:
            if neighbor in visited:
                continue
            visited.add(neighbor)
            distance = distances[neighbor]
            lower_bound = -retained[0][0]
            if len(retained) < ef or lower_bound > distance:
                heapq.heappush(candidates, (distance, neighbor))
                heapq.heappush(retained, (-distance, neighbor))
                if len(retained) > ef:
                    heapq.heappop(retained)
    return visited


def reachable(graph, entry):
    todo = [entry]
    seen = {entry}
    while todo:
        node = todo.pop()
        for neighbor in graph[node]:
            if neighbor not in seen:
                seen.add(neighbor)
                todo.append(neighbor)
    return seen


class FullEnumerationContractTest(unittest.TestCase):
    def test_pinned_source_has_required_capacity_semantics(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertIn("top_candidates.size() < ef || lowerBound > dist", text)
        self.assertIn("candidate_dist > lowerBound", text)
        self.assertIn("top_candidates.size() > ef", text)
        self.assertRegex(text, re.compile(r"bool bare_bone_search\s*=\s*!num_deleted_\s*&&\s*!isIdAllowed"))

    def test_connected_graphs_enumerate_all_nodes_at_ef_n(self):
        rng = random.Random(991)
        for n in (1, 2, 7, 31, 129):
            for repetition in range(12):
                graph = [set() for _ in range(n)]
                # A random spanning tree guarantees directed reachability because
                # both arcs are installed. Extra arcs exercise cycles.
                for node in range(1, n):
                    parent = rng.randrange(node)
                    graph[node].add(parent)
                    graph[parent].add(node)
                for _ in range(n * 3):
                    a, b = rng.randrange(n), rng.randrange(n)
                    if a != b:
                        graph[a].add(b)
                        graph[b].add(a)
                distances = [rng.random() + i * 1e-12 for i in range(n)]
                self.assertEqual(reachable(graph, 0), set(range(n)))
                self.assertEqual(full_ef_search(graph, 0, distances, n), set(range(n)))

    def test_directed_reachability_is_sufficient(self):
        graph = [{1}, {2}, {3}, {4}, set()]
        distances = [9.0, 1.0, 8.0, 2.0, 7.0]
        self.assertEqual(full_ef_search(graph, 0, distances, 5), set(range(5)))

    def test_disconnected_graph_fails_closed(self):
        graph = [{1}, {0}, {3}, {2}]
        distances = [4.0, 3.0, 2.0, 1.0]
        self.assertNotEqual(reachable(graph, 0), set(range(4)))
        self.assertNotEqual(full_ef_search(graph, 0, distances, 4), set(range(4)))

    def test_preconditions_reject_count_deletion_or_filter(self):
        def gate(current_count, max_elements, deleted, has_filter):
            return current_count == max_elements == 100000 and deleted == 0 and not has_filter

        self.assertTrue(gate(100000, 100000, 0, False))
        self.assertFalse(gate(99999, 100000, 0, False))
        self.assertFalse(gate(100000, 100000, 1, False))
        self.assertFalse(gate(100000, 100000, 0, True))


if __name__ == "__main__":
    unittest.main()
