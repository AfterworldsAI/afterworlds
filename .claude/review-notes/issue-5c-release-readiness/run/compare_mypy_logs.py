"""Compare the (file, message) error multisets of two mypy logs given as paths."""

import collections
import re
import sys

pat = re.compile(r"((?:test_\w+|conftest)\.py):(\d+): error: (.*)$")


def errs(path: str) -> collections.Counter[tuple[str, str]]:
    out: collections.Counter[tuple[str, str]] = collections.Counter()
    for line in open(path, encoding="utf-8"):
        m = pat.search(line.rstrip())
        if m:
            out[(m[1], m[3])] += 1
    return out


a, b = errs(sys.argv[1]), errs(sys.argv[2])
print("first", sum(a.values()), "second", sum(b.values()), "identical", a == b)
for k in sorted(set(a) | set(b)):
    if a[k] != b[k]:
        print(a[k], "->", b[k], k)
sys.exit(0 if a == b else 1)
