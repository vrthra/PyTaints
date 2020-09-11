import taintwrappers as w

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
        ...
        #print(' ' * len(self.TAINTS), self.t(), repr(p), repr(val), 'taint:',hasattr(val, 'taint'), 'bgtaint:', t.t())

    def __call__(self, val):
        if val is None: return val
        val_taint = val.taint if hasattr(val, 'taint') else None
        bg_taint = self.t()[1]
        cur_taint = taint_policy(val_taint, bg_taint)
        if hasattr(val, 'taint'):
            val.taint = cur_taint
            return val
        if isinstance(val, int): return w.tint(val, cur_taint)
        if isinstance(val, bool): return w.tbool(val, cur_taint)
        if isinstance(val, tuple): return w.ttuple(val, cur_taint)
        if isinstance(val, str): return w.tstr(val, cur_taint)
        if isinstance(val, list): return w.tlist(val, cur_taint)
        if isinstance(val, float): return w.tfloat(val, cur_taint)
        if isinstance(val, dict): return w.tdict(val, cur_taint)

        # no taints for module
        if type(val) == type(w): return val
        raise Exception ("Taint conversion unknown:" + str(type(val)))

TAINTS = Taint()
def taint_policy(taint_a, taint_b):
    if taint_a is None: return taint_b
    if taint_b is None: return taint_a
    return taint_a

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
    return expr

T_ = taint_expr__
