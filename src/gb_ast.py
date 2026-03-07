import textwrap as tw
import syntax
from expr import Expr
from lexer import Token

INDENT = " " * 4

class ASTNode:
    def __init__(self, scope: list['ASTNode'], *alt_scope):
        self.scope = [scope] + list(alt_scope)

    def nun_scopes(self) -> int:
        return len(self.scope)

    def content(self, alt=0) -> str:
        return "\n".join([str(c) for c in self.scope[alt]])

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
    def __init__(self, cond: ASTNode, scope: list[ASTNode], else_scope: list[ASTNode]):
        super().__init__(scope, else_scope)
        self.cond = cond

    def __str__(self):
        in_if = tw.indent(self.content(), INDENT)
        in_else = tw.indent(self.content(1), INDENT)
        return f"if({self.cond}) {{\n{in_if}\n}} else {{\n{in_else}\n}}"

class ASTNodeExpression(ASTNode):
    def __init__(self, expr: Expr):
        self.expr = expr
        super().__init__(scope=[])

    def __str__(self):
        return str(self.expr.optimize())

class ASTNodeText(ASTNode):
    def __init__(self, text: str):
        self.text = text
        super().__init__(scope=[])

    def __str__(self):
        return self.text

class ASTNodeJumpHandler(ASTNode):
    def __init__(self, inst: syntax.InstJump):
        super().__init__(scope=[])


def make_scope_for_func(content_begin: Token,
                        regmap: syntax.TypeRegmap,
                        stack: syntax.TypeStack,
                        token_end: Token | None=None) -> list:
    scope: list = []
    tok = content_begin
    while tok is not None and tok is not token_end:
        if tok.jump_addr:
            if tok.if_cond_unmet:
                after = tok.next_feature
                cond = ASTNodeExpression(
                    Expr(syntax.CONDITIONS[tok.inst.cond],
                         regmap[syntax.Reg.A], Expr(0)
                    )
                )

                if_scope = make_scope_for_func(
                    tok.jump_addr, regmap, stack, token_end=after
                )

                else_scope = make_scope_for_func(
                    tok.if_cond_unmet, regmap, stack, token_end=after
                )

                # NOTE: we intentionally reverse the condition statement
                # and flip the if and else
                scope.append(ASTNodeIfStmt(cond, else_scope, if_scope))
                tok = after
            else:
                tok = tok.jump_addr
        else:
            expr = tok.inst.dry_run(regmap)
            if isinstance(tok.inst, syntax.InstStack):
                tok.inst.update_stack(regmap, stack)
            if expr:
                scope.append(ASTNodeExpression(expr))
            tok = tok.next_feature

    return scope

def build_ast(explored_tokens) -> ASTNode:
    scope: list = []
    regmap, stack = syntax.create_initial_regmap()
    for func, content in explored_tokens.items():
        func_scope = make_scope_for_func(content[0], regmap, stack)
        scope.append(ASTNodeFunc(name=func, scope=func_scope))
    return ASTNodeInitial(scope=scope)
