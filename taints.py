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

class TaintedObject:
    def __init__(self, o, taint):
        self.o = o
        self.taint = taint

    def __getitem__(self, tainted_key):
        if isinstance(tainted_key, slice):
            tainted_start = tainted_key.start
            tainted_stop = tainted_key.stop
            tainted_step = tainted_key.step
            taint_start, start = unwrap(tainted_start)
            taint_stop, stop = unwrap(tainted_stop)
            taint_step, step = unwrap(tainted_stop)
            return TaintedObject(self.o[slice(start, stop, step)], TaintPolicy(taint_start, taint_stop, taint_step, self.taint))

        else:
            taint, key = unwrap(tainted_key)
            return TaintedObject(self.o[key], TaintPolicy(taint, self.taint))

    def in_(self, val):
        if isinstance(val, TaintedObject):
            taint, val = unwrap(val)
            return TaintedObject(val, TaintPolicy(taint, self.taint))
        return TaintedObject(val, self.taint)


    def __add__(self, other):
        t, o = unwrap(self.o)
        tt, ot = unwrap(other)
        return TaintedObject((o + ot), TaintPolicy(t, tt))

    def __repr__(self):
        t, o = unwrap(self.o)
        return 'T[%s]' % (repr(o))

    def __bool__(self):
        t, o = unwrap(self.o)
        return bool(o)

    def __getattr__(self, name):
        return getattr(self.o, name)

class TaintedException(Exception):
    def __init__(self, e):
        self.e = e

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
        ...
        #print(' ' * len(self.TAINTS), self.t(), repr(p), repr(val), 'taint:',hasattr(val, 'taint'), 'bgtaint:', t.t())

    def __call__(self, val):
        if isinstance(val, Exception):
            return TaintedException(val)
        # Always produce a new object.
        # TODO: this should simple be a single type custom object that is a
        # container for all kinds of tainted values. It should define
        # all dunder methods which extract values and pass on the
        # resulting taints just like proxy.

        if val is None: return val
        val_taint = val.taint if hasattr(val, 'taint') else None
        bg_taint = self.t()[1]
        cur_taint = TaintPolicy(val_taint, bg_taint)
        return TaintedObject(val, cur_taint)

TAINTS = Taint()

import traceback
class T_method:
    def __init__(self, method_name, *args):
        self.method_name = method_name

    def __enter__(self):
        taint = None # method by default does not have a base taint.
        TAINTS.push([self.method_name, taint])
        TAINTS.p_('*>')
        return TAINTS

    def __exit__(self, typ, val, tb):
        p = '*<'
        if isinstance(val, Exception):
             p = '*<' + str(val)
             traceback.print_tb(tb)
        TAINTS.p_(p)
        TAINTS.pop()

T_method__ = T_method

class T_scope:
    def __init__(self, scope_name, num, taint_obj):
        taint = taint_obj.t()[1]
        TAINTS.push([scope_name, taint])
        TAINTS.p_('> %s %s' % (scope_name, num))

    def __enter__(self):
        return TAINTS

    def __exit__(self, typ, val, tb):
        p = '*<'
        if isinstance(val, Exception):
             p = '*<' + str(val)
             traceback.print_tb(tb)
        TAINTS.p_(p)
        TAINTS.pop()
T_scope__ = T_scope

def taint_expr__(expr, taint):
    taint.p('taint_expr', expr, taint)
    if hasattr(expr, 'taint'): # this is tainted
        taint.t()[1] = expr.taint
    taint.p('taint_expr', expr, taint)
    t, e =  unwrap(expr)
    return e

T_ = taint_expr__

def O(fn):
    if not isinstance(fn, type(lambda: 1)): return fn
    def proxy(*args, **kwargs):
        # TODO: Check if T_method is in operation, if it is not, then
        # check if any of the args and kwargs are tainted. If it is,
        # taint the returned value (v)
        # also, if any arguments are tainted containers, extract the
        # original object before passing it.
        v = fn(*args, **kwargs)
        return v
    return proxy

def Tx(val, taint):
    return TaintedObject(val, taint)

def unwrap(o):
    if isinstance(o, TaintedObject):
        computed_taint, original_o = unwrap(o.o)
        cur_taint = TaintPolicy(o.taint, computed_taint)
        return cur_taint, original_o
    return None, o

class TaintPolicy:
    def __init__(self, *taint):
        val = [t for t in taint if t is not None]
        self.taint = sum(val)

    def __add__(self, other):
        if other is None: return self
        return self

    def __radd__(self, other):
        if other is None: return self
        return self

    def __repr__(self):
        return 't[%s]' % repr(self.taint)
