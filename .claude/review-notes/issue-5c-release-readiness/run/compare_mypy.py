import re,collections,sys
R=".claude/review-notes/issue-5c-release-readiness/run/"
pat=re.compile(r"((?:test_\w+|conftest)\.py):(\d+): error: (.*)$")
def errs(n):
    out=collections.Counter()
    for l in open(R+n,encoding="utf-8"):
        m=pat.search(l.rstrip())
        if m: out[(m[1],m[3])]+=1
    return out
a,b=errs("mypy-consumers.log"),errs("mypy-consumers-preedit-copies.log")
print("before",sum(b.values()),"after",sum(a.values()))
for k in sorted(set(a)|set(b)):
    if a[k]!=b[k]: print(b[k],"->",a[k],k)
