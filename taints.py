from collections import UserList, UserDict
import inspect
import enum

class tint(int):
    def __new__(cls, value, *args, **kw):
        return int.__new__(cls, value)

    def __init__(self, value, taint=None, **kwargs):
        self.taint = taint

    def __repr__(self):
        s = int.__repr__(self)
        return tstr(s, taint=self.taint)

    def __str__(self):
        return tstr(int.__str__(self), taint=self.taint)

    def __int__(self):
        return int.__int__(self)

    def clear_taint(self):
        self.taint = None
        return self

    def has_taint(self):
        return self.taint is not None

    def create(self, n):
        return tint(n, taint=self.taint)

    def __add__(self, other):
        if hasattr(other, 'taint') and other.taint == "HIGH":
            pr_taint = other.taint
        else:
            pr_taint = self.taint
        return tint(int(self) + int(other) , taint=pr_taint)

class tfloat(float):
    def __new__(cls, value, *args, **kw):
        return float.__new__(cls, value)

    def __init__(self, value, taint=None, **kwargs):
        self.taint = taint

    def __repr__(self):
        s = float.__repr__(self)
        return tstr(s, taint=self.taint)

    def __str__(self):
        return tstr(float.__str__(self), taint=self.taint)

    def __float__(self):
        return float.__float__(self)

    def clear_taint(self):
        self.taint = None
        return self

    def has_taint(self):
        return self.taint is not None

    def create(self, n):
        return tfloat(n, taint=self.taint)

    def __add__(self, other):
        if hasattr(other, 'taint') and other.taint == "HIGH":
            pr_taint = other.taint
        else:
            pr_taint = self.taint
        return tfloat(float(self) + float(other) , taint=pr_taint)

class tlist(UserList):

    def __init__(self, liste, taint=None):
        self.taint_counter = {}
        self.taint = taint
        if taint == None:
             super().__init__(liste)
             for dt in self.data:
                 if hasattr(dt, 'taint'):
                     print("inc taint")
                     self.inc_taint(dt.taint)
        else:
            super().__init__({})
            for dt in liste:
                if isinstance(dt, str):
                    self.data.append(tstr(dt, taint))
                elif isinstance(dt, int):
                    self.data.append(tint(dt, taint))
                elif isinstance(dt, float):
                    pass
                self.inc_taint(taint)


        self.set_taint_helper()


    def __setitem__(self, i, item):
        if i == len(self.data):
            self.data.append(item)
        else:
            self.data[i] = item
        if hasattr(item, 'taint'):
            self.inc_taint(item.taint)

        self.set_taint_helper()


    def __getitem__(self, key):
        value = super().__getitem__(key)
        if hasattr(value, 'taint'):
            return value
        #print("wrapping the value")
        return value

    def __delitem__(self, i):
        self.pop(i)

    def pop(self, i):
        elem = super().pop(i)
        if hasattr(elem, 'taint'):
            self.dec_taint(elem.taint)
        return elem

    def remove(self, item):
        idx = super().index(item)
        elem = super().pop(idx)
        if hasattr(elem, 'taint'):
            self.dec_taint(elem.taint)


    def append(self, item):
        self.data.append(item)
        if hasattr(item, 'taint'):
            self.inc_taint(item.taint)

        self.set_taint_helper()

    def highest_taint(self):
        return self.highest_taint


    def __repr__(self):
        return f"{type(self).__name__}({super().__repr__()}, {self.highest_taint})"


    def set_taint_helper(self):
        if 'HIGH' in self.taint_counter:
           self.highest_taint = 'HIGH'
           self.taint = 'HIGH'
        elif 'LOW' in self.taint_counter:
           self.highest_taint = 'LOW'
           self.taint = 'LOW'
        else:
           self.highest_taint = None


    def inc_taint(self, taint):
        if not taint in self.taint_counter:
            self.taint_counter[taint] = 1
        else:
            self.taint_counter[taint] += 1


    def dec_taint(self, taint):
        self.taint_counter[taint] -= 1
        if self.taint_counter[taint] == 0:
            del self.taint_counter[taint]
            self.set_taint_helper()

class tdict(UserDict):
    def __init__(self, dicte, taint=None):
        self.taint_counter = {}
        self.taint = taint
        if taint == None:
             super().__init__(dicte)
        else:
             super().__init__({})
             for key, value in dicte.items():
                 if isinstance(value, str):
                     self.data[key] = tstr(value, taint)
                 elif isinstance(value, int):
                     self.data[key] = tint(value, taint)
                 elif isinstance(value, float):
                    pass
                 self.inc_taint(taint)

        self.set_taint_helper()

    def __delitem__(self, key):
        value = self.data.pop(key)
        if hasattr(value, 'taint'):
            self.dec_taint(value.taint)
        self.set_taint_helper()

    def __setitem__(self, key, value):
        if key in self:
            old_val = self.data[key]
            if hasattr(old_val, 'taint'):
                self.dec_taint(old_val.taint)
        super().__setitem__(key, value)
        if hasattr(value, 'taint'):
            self.inc_taint(value.taint)
        self.set_taint_helper()

    def __repr__(self):
        return f"{type(self).__name__}({super().__repr__()}, {self.highest_taint})"

    def set_taint_helper(self):
        if 'HIGH' in self.taint_counter:
           self.highest_taint = 'HIGH'
           self.taint = 'HIGH'
        elif 'LOW' in self.taint_counter:
           self.highest_taint = 'LOW'
           self.taint = 'LOW'
        else:
           self.highest_taint = None


    def inc_taint(self, taint):
        if not taint in self.taint_counter:
            self.taint_counter[taint] = 1
        else:
            self.taint_counter[taint] += 1


    def dec_taint(self, taint):
        self.taint_counter[taint] -= 1
        if self.taint_counter[taint] == 0:
            del self.taint_counter[taint]
            self.set_taint_helper()


class ttuple(tuple):
    def __new__(cls, value, *args, **kw):
        return tuple.__new__(cls, value)

    def __init__(self, value, taint=None, **kwargs):
        self.taint = taint

class tbool(int):
    def __new__(cls, value, *args, **kw):
        return int.__new__(cls, value)

    def __init__(self, value, taint=None, **kwargs):
        self.taint = taint


class tstr_(str):
    def __new__(cls, value, *args, **kw):
        return super(tstr_, cls).__new__(cls, value)

class tstr(tstr_):
    def __init__(self, value, taint=None, parent=None, **kwargs):
        self.parent = parent
        l = len(self)
        if taint is None:
            taint = 0
        self.taint = list(range(taint, taint + l)) if isinstance(
            taint, int) else taint
        assert len(self.taint) == l

    def __repr__(self):
        return self

    def __str__(self):
        return str.__str__(self)

class tstr(tstr):
    def untaint(self):
        self.taint = [None] * len(self)
        return self

    def has_taint(self):
        return any(True for i in self.taint if i is not None)

    def taint_in(self, gsentence):
        return set(self.taint) <= set(gsentence.taint)



class tstr(tstr):
    def create(self, res, taint):
        return tstr(res, taint, self)



class tstr(tstr):
    def __getitem__(self, key):
        res = super().__getitem__(key)
        if isinstance(key, int):
            key = len(self) + key if key < 0 else key
            return self.create(res, [self.taint[key]])
        elif isinstance(key, slice):
            return self.create(res, self.taint[key])
        else:
            assert False

class tstr(tstr):
    def __iter__(self):
        return tstr_iterator(self)

class tstr_iterator():
    def __init__(self, tstr):
        self._tstr = tstr
        self._str_idx = 0

    def __next__(self):
        if self._str_idx == len(self._tstr):
            raise StopIteration
        # calls tstr getitem should be tstr
        c = self._tstr[self._str_idx]
        assert isinstance(c, tstr)
        self._str_idx += 1
        return c

class tstr(tstr):
    def __add__(self, other):
        if isinstance(other, tstr):
            return self.create(str.__add__(self, other),
                               (self.taint + other.taint))
        else:
            return self.create(str.__add__(self, other),
                               (self.taint + [-1 for i in other]))

class tstr(tstr):
    def __radd__(self, other):
        if other:
            taint = other.taint if isinstance(other, tstr) else [
                None for i in other]
        else:
            taint = []
        return self.create(str.__add__(other, self), (taint + self.taint))

class tstr(tstr):
    class TaintException(Exception):
        pass

    def x(self, i=0):
        if not self.taint:
            raise tstr.TaintException('Invalid request idx')
        if isinstance(i, int):
            return [self[p]
                    for p in [k for k, j in enumerate(self.taint) if j == i]]
        elif isinstance(i, slice):
            r = range(i.start or 0, i.stop or len(self), i.step or 1)
            return [self[p]
                    for p in [k for k, j in enumerate(self.taint) if j in r]]

class tstr(tstr):
    def replace(self, a, b, n=None):
        old_taint = self.taint
        b_taint = b.taint if isinstance(b, tstr) else [None] * len(b)
        mystr = str(self)
        i = 0
        while True:
            if n and i >= n:
                break
            idx = mystr.find(a)
            if idx == -1:
                break
            last = idx + len(a)
            mystr = mystr.replace(a, b, 1)
            partA, partB = old_taint[0:idx], old_taint[last:]
            old_taint = partA + b_taint + partB
            i += 1
        return self.create(mystr, old_taint)

class tstr(tstr):
    def _split_helper(self, sep, splitted):
        result_list = []
        last_idx = 0
        first_idx = 0
        sep_len = len(sep)

        for s in splitted:
            last_idx = first_idx + len(s)
            item = self[first_idx:last_idx]
            result_list.append(item)
            first_idx = last_idx + sep_len
        return result_list

    def _split_space(self, splitted):
        result_list = []
        last_idx = 0
        first_idx = 0
        sep_len = 0
        for s in splitted:
            last_idx = first_idx + len(s)
            item = self[first_idx:last_idx]
            result_list.append(item)
            v = str(self[last_idx:])
            sep_len = len(v) - len(v.lstrip(' '))
            first_idx = last_idx + sep_len
        return result_list

    def rsplit(self, sep=None, maxsplit=-1):
        splitted = super().rsplit(sep, maxsplit)
        if not sep:
            return self._split_space(splitted)
        return self._split_helper(sep, splitted)

    def split(self, sep=None, maxsplit=-1):
        splitted = super().split(sep, maxsplit)
        if not sep:
            return self._split_space(splitted)
        return self._split_helper(sep, splitted)

class tstr(tstr):
    def strip(self, cl=None):
        return self.lstrip(cl).rstrip(cl)

    def lstrip(self, cl=None):
        res = super().lstrip(cl)
        i = self.find(res)
        return self[i:]

    def rstrip(self, cl=None):
        res = super().rstrip(cl)
        return self[0:len(res)]


class tstr(tstr):
    def expandtabs(self, n=8):
        parts = self.split('\t')
        res = super().expandtabs(n)
        all_parts = []
        for i, p in enumerate(parts):
            all_parts.extend(p.taint)
            if i < len(parts) - 1:
                l = len(all_parts) % n
                all_parts.extend([p.taint[-1]] * l)
        return self.create(res, all_parts)

class tstr(tstr):
    def join(self, iterable):
        mystr = ''
        mytaint = []
        sep_taint = self.taint
        lst = list(iterable)
        for i, s in enumerate(lst):
            staint = s.taint if isinstance(s, tstr) else [None] * len(s)
            mytaint.extend(staint)
            mystr += str(s)
            if i < len(lst) - 1:
                mytaint.extend(sep_taint)
                mystr += str(self)
        res = super().join(iterable)
        assert len(res) == len(mystr)
        return self.create(res, mytaint)

class tstr(tstr):
    def partition(self, sep):
        partA, sep, partB = super().partition(sep)
        return (self.create(partA, self.taint[0:len(partA)]),
                self.create(sep, self.taint[len(partA):len(partA) + len(sep)]),
                self.create(partB, self.taint[len(partA) + len(sep):]))

    def rpartition(self, sep):
        partA, sep, partB = super().rpartition(sep)
        return (self.create(partA, self.taint[0:len(partA)]),
                self.create(sep, self.taint[len(partA):len(partA) + len(sep)]),
                self.create(partB, self.taint[len(partA) + len(sep):]))

class tstr(tstr):
    def ljust(self, width, fillchar=' '):
        res = super().ljust(width, fillchar)
        initial = len(res) - len(self)
        if isinstance(fillchar, tstr):
            t = fillchar.x()
        else:
            t = -1
        return self.create(res, [t] * initial + self.taint)

    def rjust(self, width, fillchar=' '):
        res = super().rjust(width, fillchar)
        final = len(res) - len(self)
        if isinstance(fillchar, tstr):
            t = fillchar.x()
        else:
            t = -1
        return self.create(res, self.taint + [t] * final)

class tstr(tstr):
    def swapcase(self):
        return self.create(str(self).swapcase(), self.taint)

    def upper(self):
        return self.create(str(self).upper(), self.taint)

    def lower(self):
        return self.create(str(self).lower(), self.taint)

    def capitalize(self):
        return self.create(str(self).capitalize(), self.taint)

    def title(self):
        return self.create(str(self).title(), self.taint)

def taint_include(gword, gsentence):
    return set(gword.taint) <= set(gsentence.taint)


def make_str_wrapper(fun):
    def proxy(*args, **kwargs):
        res = fun(*args, **kwargs)
        return res
    return proxy

import types
tstr_members = [name for name, fn in inspect.getmembers(tstr, callable)
                if isinstance(fn, types.FunctionType) and fn.__qualname__.startswith('tstr')]

for name, fn in inspect.getmembers(str, callable):
    if name not in set(['__class__', '__new__', '__str__', '__init__',
                        '__repr__', '__getattribute__']) | set(tstr_members):
        setattr(tstr, name, make_str_wrapper(fn))


def make_str_abort_wrapper(fun):
    def proxy(*args, **kwargs):
        raise tstr.TaintException('%s Not implemented in TSTR' % fun.__name__)
    return proxy

def trace_return():
    METHOD_NUM_STACK.pop()

def trace_set_method(method):
    set_current_method(method, len(METHOD_NUM_STACK), METHOD_NUM_STACK[-1][0])
    
class in_wrap:
    def __init__(self, s):
        self.s = s

    def in_(self, s):
        return self.s in s

def taint_wrap__(st):
    if isinstance(st, str):
        return in_wrap(st)
    else:
        return st


class Taint:
    def __init__(self):
        self.TAINTS = [None]

    def push(self, v):
        self.TAINTS.append(v)

    def pop(self):
        self.TAINTS.pop()

    def t(self):
        return self.TAINTS[-1]

    def p_(self, p):
        print(' ' * len(self.TAINTS), p, self.t())

    def p(self, p, val, t):
        print(' ' * len(self.TAINTS), self.t(), repr(p), repr(val), 'taint:',hasattr(val, 'taint'), 'bgtaint:', t.t())

    def __call__(self, val):
        if val is None: return val
        # if hasattr(val, 'taint'): print('tainted: A')
        # also check if self.t() has a taint
        # if self.t()[1] is not None: print('tainted: B')
        # TODO: if either val or self.t() has taint
        # then, make val the more tainted of the two.
        if hasattr(val, 'taint'): return val
        if self.t()[1] is None: return val

        if isinstance(val, int): return tint(val, '1')
        if isinstance(val, bool): return tbool(val, '1')
        if isinstance(val, tuple): return ttuple(val, '1')
        if isinstance(val, list): return tlist
        if isinstance(val, float): return tfloat
        if isinstance(val, dict): return tdict
        raise Exception ("Taint conversion unknown:" + str(type(val)))

TAINTS = Taint()

from contextlib import contextmanager
@contextmanager
def T_method__(method_name, *args):
    taint = None # method by default does not have a base taint.
    TAINTS.push([method_name, taint])
    TAINTS.p_('>*')
    try:
        yield TAINTS
    finally:
        TAINTS.p_('<*')
        TAINTS.pop()

@contextmanager
def T_scope__(scope_name, num, taint_obj):
    taint = taint_obj.t()[1]
    TAINTS.push([scope_name, taint])
    TAINTS.p_('>')
    try:
        yield TAINTS
    finally:
        TAINTS.p_('<')
        TAINTS.pop()

def taint_expr__(expr, taint):
    taint.p('taint_expr', expr, taint)
    if hasattr(expr, 'taint'): # this is tainted
        taint.t()[1] = expr.taint
    taint.p('taint_expr', expr, taint)
    return expr

def wrap_input(inputstr):
    return tstr(inputstr, parent=None)

