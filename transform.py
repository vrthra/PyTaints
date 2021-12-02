import ast

methods = []
Epsilon = '-'
NoEpsilon = '='
TaintName = 'T'
TaintFunc = 'O'
TaintAssign = 'T'
TaintWrap = 'taint_wrap__'
TaintExpr = 'T_'
TaintedMethod = 'T_method__'
TaintedScope = 'T_scope__'

class TaintRewriter(ast.NodeTransformer):
    def I(self, node):
        return ast.Call(func=ast.Name(id=TaintName, ctx=ast.Load()), args=[node], keywords=[])

    def O(self, node):
        if isinstance(node, ast.Attribute):
            name = "%s.%s" % (node.attr, node.value.id)
        elif isinstance(node, ast.Name):
            name = node.id
        else:
            assert False
        return ast.Call(func=ast.Name(id=TaintFunc, ctx=ast.Load()), args=[
            node, ast.Name(id=TaintName, ctx=ast.Load()),
            ast.Str(name)
            ], keywords=[])



    def init_counters(self):
        self.if_counter = 0
        self.while_counter = 0

    def visit_BoolOp(self, tree_node):
        self.generic_visit(tree_node)
        return self.I(tree_node)

    #def visit_NamedExpr(self, tree_node):
    #    self.generic_visit(tree_node)
    #    return self.I(tree_node)

    def visit_BinOp(self, tree_node):
        self.generic_visit(tree_node)
        return self.I(tree_node)

    def visit_UnaryOp(self, tree_node):
        self.generic_visit(tree_node)
        return self.I(tree_node)

    # Lambda
    # IfExp

    def visit_Dict(self, tree_node):
        self.generic_visit(tree_node)
        return self.I(tree_node)

    def visit_Set(self, tree_node):
        self.generic_visit(tree_node)
        return self.I(tree_node)


    def visit_ListComp(self, tree_node):
        gs = []
        for g in tree_node.generators:
             # (expr target, expr iter, expr* ifs)
             self.generic_visit(ast.Module(g.iter)).body
        return self.I(tree_node)

    # ListComp
    # SetComp
    # DictComp
    # GeneratorExp
    # Await
    # Yield
    # YieldFrom

    def visit_Compare(self, tree_node):
        left = tree_node.left
        if not tree_node.ops or not isinstance(tree_node.ops[0], ast.In):
            self.generic_visit(tree_node)
            return self.I(tree_node)
        mod_val = ast.Call(func=ast.Attribute(value=self.wrap(left), attr='in_'), args=tree_node.comparators, keywords=[])
        return mod_val

    # Call(expr func, expr* args, keyword* keywords)
    # what happens when an empty call is made? Do we
    # transfer taints?
    def visit_Call(self, tree_node):
        #self.generic_visit(tree_node)
        # call has to be handled differently.
        tree_node.func = self.O(tree_node.func)
        my_args = []
        for arg in tree_node.args:
            a = self.generic_visit(ast.Module(arg))
            my_args.append(a.body)
        tree_node.args = my_args
        return self.I(tree_node)

    # FormattedValue(expr value, int? conversion, expr? format_spec)
    # JoinedStr(expr* values)
    def visit_Constant(self, tree_node):
        self.generic_visit(tree_node)
        return self.I(tree_node)

    def visit_Num(self, tree_node):
        self.generic_visit(tree_node)
        return self.I(tree_node)

    def visit_Str(self, tree_node):
        self.generic_visit(tree_node)
        return self.I(tree_node)

    def visit_Bytes(self, tree_node):
        self.generic_visit(tree_node)
        return self.I(tree_node)

    def visit_NameConstant(self, tree_node):
        self.generic_visit(tree_node)
        return self.I(tree_node)

    #- the following expression can appear in assignment context
    # Attribute(expr value, identifier attr, expr_context ctx)
    # Subscript(expr value, slice slice, expr_context ctx)
    # Starred(expr value, expr_context ctx)
    # Name(identifier id, expr_context ctx)
    def visit_Name(self, tree_node):
        self.generic_visit(tree_node)
        return self.I(tree_node)

    def visit_List(self, tree_node):
        self.generic_visit(tree_node)
        return self.I(tree_node)

    def visit_Tuple(self, tree_node):
        self.generic_visit(tree_node)
        return self.I(tree_node)



    # TODO: not quite clear why I have to wrap the node.value in a module
    # to make visit_String visit it.
    def visit_Assign(self, tree_node):
        v = self.generic_visit(ast.Module(tree_node.value))
        tree_node.value = v.body
        return tree_node

    def visit_AugAssign(self, tree_node):
        v = self.generic_visit(ast.Module(tree_node.value))
        tree_node.value = v.body
        return tree_node

    def visit_AnnAssign(self, tree_node):
        v = self.generic_visit(ast.Module(tree_node.value))
        tree_node.value = v.body
        return tree_node

    # Control Flow
    def wrap(self, node):
        return ast.Call(func=ast.Name(id=TaintWrap, ctx=ast.Load()), args=[node], keywords=[])

    def wrap_in_method(self, body, args):
        method_name_expr = ast.Str(methods[-1])
        my_args = ast.List(args.args, ast.Load())
        args = [method_name_expr, my_args]
        scope_expr = ast.Call(func=ast.Name(id=TaintedMethod, ctx=ast.Load()), args=args, keywords=[])
        # we expect the method__ to push in the taint in the beginning, and pop out when it is done.
        return [ast.With(items=[ast.withitem(scope_expr, ast.Name(id=TaintName))], body=body)]

    def visit_FunctionDef(self, tree_node):
        self.init_counters()
        methods.append(tree_node.name)
        body = self.generic_visit(ast.Module(tree_node.body)).body
        tree_node.body = self.wrap_in_method(body, tree_node.args)
        return tree_node

    # TaintedScope should prepare an empty taint space in the TAINT stack which
    # will be populated by the next TaintExpr call. (TaintExpr calls will never
    # pop or push, but only change the top cell).
    def wrap_in_outer(self, name, counter, node):
        #return node # <- to disable
        name_expr = ast.Str(name)
        counter_expr = ast.Num(counter)
        args = [name_expr, counter_expr, ast.Name(id=TaintName)]
        scope_expr = ast.Call(func=ast.Name(id=TaintedScope, ctx=ast.Load()), args=args, keywords=[])
        return ast.With(items=[ast.withitem(scope_expr, ast.Name(id=TaintName))], body=[node])

    def wrap_expr_in_call(self, name, node, argnames):
        nargs = [ast.Name(id=a, ctx=ast.Load()) for a in argnames]
        return ast.Call(func=ast.Name(id=name, ctx=ast.Load()), args=[node, *nargs ], keywords=[])

    def visit_If(self, tree_node):
        self.if_counter += 1
        counter = self.if_counter
        body = []
        for node in tree_node.body:
            n = self.generic_visit(ast.Module(node))
            body.append(n.body)
        tree_node.body = body
        else_body = []
        for node in tree_node.orelse:
            n = self.generic_visit(ast.Module(node))
            else_body.append(n.body)
        tree_node.orelse = else_body

        test = self.generic_visit(ast.Module(tree_node.test)).body
        tree_node.test = self.wrap_expr_in_call(TaintExpr, test, [ ast.Name(id=TaintName)])
        return self.wrap_in_outer('if', counter, tree_node)

    def visit_While(self, tree_node):
        self.while_counter += 1
        counter = self.while_counter
        body = []
        for node in tree_node.body:
            n = self.generic_visit(ast.Module(node))
            body.append(n.body)
        tree_node.body = body
        assert not tree_node.orelse
        test = self.generic_visit(ast.Module(tree_node.test)).body
        tree_node.test = self.wrap_expr_in_call(TaintExpr, test, [ast.Name(id=TaintName)])
        return self.wrap_in_outer('while', counter, tree_node)


    def visit_For(self, tree_node):
        self.while_counter += 1
        counter = self.while_counter
        body = []
        for node in tree_node.body:
            n = self.generic_visit(ast.Module(node))
            body.append(n.body)
        tree_node.body = body
        tree_node.iter = self.wrap_expr_in_call(TaintExpr, tree_node.iter, [ast.Name(id=TaintName)])
        return self.wrap_in_outer('for', counter, tree_node)


def rewrite(src):
    v = ast.fix_missing_locations(TaintRewriter().visit(ast.parse(src)))
    header = """\
import taints
from taints import T_method__, T_scope__
from taints import T_, O, Tx
from taints import taint_wrap__
"""
    source = ast.dump(v, indent=4)
    methods_s = ',\n'.join([repr(s) for s in methods])
    footer = """\
for method in [%s]:
    taints.hook_method(method)

if __name__ == "__main__":
    import sys
    js = []
    for arg in sys.argv[1:]:
        with open(arg) as f:
            mystring = f.read().strip().replace('\\n', ' ')
        v = main(Tx(mystring))
        print(v)
""" % methods_s
    return "%s\n%s\n%s" % (header, source, footer)

def read_it(fn):
    with open(fn) as f: return f.read()

if __name__ == '__main__':
    import sys
    print(rewrite('\n'.join(read_it(sys.argv[1]).split('\n'))))
