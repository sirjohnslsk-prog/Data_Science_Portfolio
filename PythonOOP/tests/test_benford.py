import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benford_analyzer import first_digit, first_two_digits, second_digit, expected_probabilities


def test_digit_extractors():
    x = np.array([1.23, 98.7, 0.0456, 700])
    assert first_digit(x).tolist() == [1, 9, 4, 7]
    assert first_two_digits(x).tolist() == [12, 98, 45, 70]
    assert second_digit(x).tolist() == [2, 8, 5, 0]


def test_probabilities_sum_to_one():
    for name in ["first_digit", "second_digit", "first_two_digits"]:
        _, p = expected_probabilities(name)
        assert np.isclose(p.sum(), 1.0)
