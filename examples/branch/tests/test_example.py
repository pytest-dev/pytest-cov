from example import (
  sum_all_numbers,
  sum_only_positive_numbers,
  sum_only_negative_numbers
)


def test_sum_all_numbers():
    assert sum_all_numbers(5, 5) == 10

def test_sum_only_positive_numbers():
    assert sum_only_positive_numbers(2, 2) == 4
    assert sum_only_positive_numbers(-1, 2) is None

def test_sum_only_negative_numbers():
    assert sum_only_negative_numbers(-2, -2) == -4
    assert sum_only_negative_numbers(-1, 2) is None
