import textwrap as tw
import syntax
from expr import Expr
from lexer import Token

INDENT = " " * 4

class ASTNode:
    def __init__(self, scope: list['ASTNode']):
        self.scope = scope

    def content(self) -> str:
        return "\n".join([str(c) for c in self.scope])

    def __str__(self):
        return "???"

class ASTNodeInitial(ASTNode):
    def __str__(self):
        return self.content()

class ASTNodeFunc(ASTNode):
    def __init__(self, name: str, scope: list[ASTNode]):
        super().__init__(scope)
        self.name = name

    def __str__(self):
        return f"{self.name} {{\n{tw.indent(self.content(), INDENT)}\n}}"

class ASTNodeLoopStmt(ASTNode):
    def __init__(self, cond: ASTNode, scope: list[ASTNode]):
        super().__init__(scope)
        self.cond = cond

    def __str__(self):
        return f"while({self.cond}) {{\n{tw.indent(self.content(), INDENT)}\n}}"

class ASTNodeIfStmt(ASTNode):
    def __init__(self, cond: ASTNode, scope: list[ASTNode]):
        super().__init__(scope)
        self.cond = cond

    def __str__(self):
        return f"if({self.cond}) {{\n{tw.indent(self.content(), INDENT)}\n}}"

class ASTNodeExpression(ASTNode):
    def __init__(self, expr: Expr):
        self.expr = expr
        super().__init__(scope=[])

    def __str__(self):
        return str(self.expr)

class ASTNodeText(ASTNode):
    def __init__(self, text: str):
        self.text = text
        super().__init__(scope=[])

    def __str__(self):
        return self.text

class ASTNodeJumpHandler(ASTNode):
    def __init__(self, inst: syntax.InstJump):
        super().__init__(scope=[])


def make_scope_for_func(content: list[Token], regmap: syntax.TypeRegmap) -> list:
    scope: list = []
    for tok in content:
        expr = tok.inst.dry_run(regmap)
        if expr:
            scope.append(ASTNodeExpression(expr))
    return scope

def build_ast(explored_tokens) -> ASTNode:
    scope: list = []
    regmap: syntax.TypeRegmap = syntax.create_initial_regmap()
    for func, content in explored_tokens.items():
        func_scope = make_scope_for_func(content, regmap)
        scope.append(ASTNodeFunc(name=func, scope=func_scope))
    return ASTNodeInitial(scope=scope)
