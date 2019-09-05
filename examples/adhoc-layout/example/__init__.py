
import sys

PY2 = sys.version_info[0] == 2


if PY2:
    def add(a, b):
        return b + a

else:
    def add(a, b):
        return a + b
