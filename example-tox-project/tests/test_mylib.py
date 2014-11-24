
import mylib


def test_add():
    assert mylib.add(1, 1) == 2
    assert not mylib.add(0, 1) == 2
