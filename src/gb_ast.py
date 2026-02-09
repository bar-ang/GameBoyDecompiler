from expr import Expr
from lr35902dis import lr35902 as disassembler

class ASTNode:
    def __init__(self, op, scope=[]):
        self.op = op
        self.scope = scope

def astBuilder(explored_tokens):
    pass




