
import sys

PY3 = sys.version_info[0] == 3


if PY3:
    def add(a, b):
        return a + b

else:
    def add(a, b):
        return b + a
