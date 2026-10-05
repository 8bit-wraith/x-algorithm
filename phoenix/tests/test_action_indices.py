"""Dependency-free regression tests for the actual sequence conversion loop.

Run: python3 -m unittest discover -s phoenix/tests -p test_action_indices.py
"""
import ast
from pathlib import Path
import unittest


class Matrix:
    def __init__(self, columns):
        self.rows = [[0.0] * columns]

    def __setitem__(self, position, value):
        row, column = position
        self.rows[row][column] = value


class ActionIndicesTest(unittest.TestCase):
    def convert(self, actions):
        source = Path(__file__).resolve().parents[1] / 'run_pipeline.py'
        tree = ast.parse(source.read_text())
        loops = [node for node in ast.walk(tree)
                 if isinstance(node, ast.For)
                 and isinstance(node.target, ast.Tuple)
                 and [getattr(n, 'id', None) for n in node.target.elts]
                 == ['act_idx_str', 'act_val']]
        self.assertEqual(len(loops), 1)
        matrix = Matrix(3)
        scope = {'item': {'actions': actions}, 'i': 0,
                 'num_actions': 3, 'history_actions': matrix}
        exec(compile(ast.Module(body=loops, type_ignores=[]), str(source), 'exec'), scope)
        return matrix.rows[0]

    def test_valid_boundaries(self):
        self.assertEqual(self.convert({'0': 0.5, '2': 1}), [0.5, 0, 1])

    def test_negative_index_does_not_alias_last_slot(self):
        self.assertEqual(self.convert({'-1': 1}), [0, 0, 0])

    def test_large_negative_index_is_ignored(self):
        self.assertEqual(self.convert({'-4': 1}), [0, 0, 0])

    def test_upper_bound_is_ignored(self):
        self.assertEqual(self.convert({'3': 1, '100': 1}), [0, 0, 0])

    def test_invalid_index_cannot_overwrite_valid_action(self):
        self.assertEqual(self.convert({'2': 0.75, '-1': 9, '3': 8}), [0, 0, 0.75])

    def test_empty_actions(self):
        self.assertEqual(self.convert({}), [0, 0, 0])


if __name__ == '__main__':
    unittest.main()
