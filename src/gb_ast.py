from expr import Expr
from lr35902dis import lr35902 as disassembler

class ASTNode:
    def __init__(self, op, scope, **args):
        self.op = op
        self.scope = scope
        self.args = args

    def __str__(self):
        content = "\n".join([str(c) for c in self.scope])
        if self.op == "initial":
            return content
        elif self.op == "func":
            return f"{self.args["name"]} {{\n\t{content}\n}}"
        assert False, "unhandled"


def build_ast(explored_tokens):
    scope = []
    for func, content in explored_tokens.items():
        scope.append(ASTNode("func", name=func, scope=[]))
    return ASTNode("initial", scope=scope)
