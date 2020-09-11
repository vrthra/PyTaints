import taintwrappers as w
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

        if isinstance(val, int): return w.tint(val, '1')
        if isinstance(val, bool): return w.tbool(val, '1')
        if isinstance(val, tuple): return w.ttuple(val, '1')
        if isinstance(val, list): return w.tlist(val, '1')
        if isinstance(val, float): return w.tfloat(val, '1')
        if isinstance(val, dict): return w.tdict(val, '1')
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

