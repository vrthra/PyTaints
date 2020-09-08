import ast
import astor

methods = []
Epsilon = '-'
NoEpsilon = '='
TaintName = '__taint__'

class InRewriter(ast.NodeTransformer):
    def wrap(self, node):
        return ast.Call(func=ast.Name(id='taint_wrap__', ctx=ast.Load()), args=[node], keywords=[])

class InRewriter(InRewriter):
    def visit_Compare(self, tree_node):
        left = tree_node.left
        if not tree_node.ops or not isinstance(tree_node.ops[0], ast.In):
            return tree_node
        mod_val = ast.Call(
            func=ast.Attribute(
                value=self.wrap(left),
                attr='in_'),
            args=tree_node.comparators,
            keywords=[])
        return mod_val

def rewrite_in(src):
    v = ast.fix_missing_locations(InRewriter().visit(ast.parse(src)))
    source = astor.to_source(v)
    return "%s" % source

class Rewriter(InRewriter):
    def init_counters(self):
        self.if_counter = 0
        self.while_counter = 0

class Rewriter(Rewriter):
    def wrap_in_method(self, body, args):
        method_name_expr = ast.Str(methods[-1])
        my_args = ast.List(args.args, ast.Load())
        args = [method_name_expr, my_args]
        scope_expr = ast.Call(func=ast.Name(id='tainted_method__', ctx=ast.Load()), args=args, keywords=[])

        # we expect the method__ to push in the taint in the beginning, and pop out when it is done.
        return [ast.With(items=[ast.withitem(scope_expr, ast.Name(id=TaintName))], body=body)]

class Rewriter(Rewriter):
    def visit_FunctionDef(self, tree_node):
        self.init_counters()
        methods.append(tree_node.name)
        self.generic_visit(tree_node)
        tree_node.body = self.wrap_in_method(tree_node.body, tree_node.args)
        return tree_node

def rewrite_def(src):
    v = ast.fix_missing_locations(Rewriter().visit(ast.parse(src)))
    return astor.to_source(v)
def read_it(fn):
    with open(fn) as f: return f.read()

class Rewriter(Rewriter):
    def wrap_in_inner(self, name, counter, val, body):
        val_expr = ast.Num(val)
        stack_iter = ast.Name(id='%s_%d_stack__' % (name, counter))
        scope_expr = ast.Call(func=ast.Name(id='tainted_scope__', ctx=ast.Load()), args=[ast.Str(stack_iter.id)], keywords=[])
        return [ast.With(items=[ast.withitem(scope_expr, ast.Name(id=TaintName))], body=body)]

class Rewriter(Rewriter):
    def wrap_expr_in_call(self, name, node, argnames):
        nargs = [ast.Name(id=a, ctx=ast.Load()) for a in argnames]
        return ast.Call(func=ast.Name(id=name, ctx=ast.Load()), args=[node, *nargs ], keywords=[])

class Rewriter(Rewriter):
    def process_if(self, tree_node, counter, val=None):
        if val is None: val = 0
        else: val += 1
        if_body = []
        self.generic_visit(tree_node.test)
        for node in tree_node.body:
            if_body.append(self.generic_visit(ast.Module(node)).body)
        tree_node.test = self.wrap_expr_in_call('taint_expr__', tree_node.test, [ ast.Name(id=TaintName)])

        tree_node.body = self.wrap_in_inner('if', counter, val, if_body)

        # else part.
        if len(tree_node.orelse) == 1 and isinstance(tree_node.orelse[0], ast.If):
            self.process_if(tree_node.orelse[0], counter, val)
        else:
            if tree_node.orelse:
                val += 1
                for node in tree_node.orelse: self.generic_visit(node)
                tree_node.orelse = self.wrap_in_inner('if', counter, val, tree_node.orelse)

class Rewriter(Rewriter):
    def visit_If(self, tree_node):
        self.if_counter += 1
        counter = self.if_counter
        #is it empty
        start = tree_node
        while start:
            if isinstance(start, ast.If):
                if not start.orelse:
                    start = None
                elif len(start.orelse) == 1:
                    start = start.orelse[0]
                else:
                    break
            else:
                break
        self.process_if(tree_node, counter=self.if_counter)
        return tree_node

class Rewriter(Rewriter):
    # AugAssign(expr target, operator op, expr value)
    # AnnAssign(expr target, expr annotation, expr? value, int simple)
    # Assign(expr* targets, expr value, string? type_comment)
    def visit_Assign(self, tree_node):
        self.generic_visit(tree_node.value)
        tree_node.value = self.wrap_expr_in_call('taint_assign__', tree_node.value, [ast.Name(id=TaintName)])
        return self.generic_visit(tree_node)

class Rewriter(Rewriter):
    def visit_While(self, tree_node):
        self.generic_visit(tree_node)
        self.while_counter += 1
        counter = self.while_counter
        tree_node.test = self.wrap_expr_in_call('taint_expr__', tree_node.test, [ast.Name(id=TaintName)])
        body = tree_node.body
        assert not tree_node.orelse
        tree_node.body = self.wrap_in_inner('while', counter, 0, body)
        return tree_node

def rewrite_cf(src):
    v = ast.fix_missing_locations(Rewriter().visit(ast.parse(src)))
    return astor.to_source(v)

def rewrite(src):
    src = ast.fix_missing_locations(InRewriter().visit(ast.parse(src)))
    v = ast.fix_missing_locations(Rewriter().visit(ast.parse(src)))
    header = """\
import json
import sys
import taints
from taints import taint_wrap__, tainted_method__, tainted_scope__, taint_expr__, taint_assign__

# taints.TAINT is an array whose last item is the current taint.
# taint_assign__ and taint_expr__ uses and modifies this array.
    """
    source = astor.to_source(v)
    footer = """
if __name__ == "__main__":
    js = []
    for arg in sys.argv[1:]:
        with open(arg) as f:
            mystring = f.read().strip().replace('\\n', ' ')
        tainted_input = taints.wrap_input(mystring)
        main(tainted_input)
"""
    return "%s\n%s\n%s" % (header, source, footer)

if __name__ == '__main__':
    import sys
    print(rewrite('\n'.join(read_it(sys.argv[1]).split('\n'))))
