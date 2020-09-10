# Taints
Both direct and indirect taints in Python.

This project can be used to produce both direct taints (operations on chosen tainted data-types produces tainted results)
For example, if `y` is tainted, and `z` is not, the following operation
```python
x = y + z
```
produces `x` which is tainted.

Further, it also supports indirect taints. For example,
```python
if (b):
   x = y + z
```
produces tainted `x` if neither `y` or `z` is tainted, but `b` is. It
accomplishes this by transforming the source code. Please execute
```bash
make test
```
for example (and inspect `tcalculator.py` which gets produced).
