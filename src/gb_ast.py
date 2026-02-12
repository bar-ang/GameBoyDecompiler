import textwrap as tw
import syntax
from expr import Expr


INDENT = " " * 4

class ASTNode:
    def __init__(self, scope):
        self.scope = scope

    def content(self):
        return "\n".join([str(c) for c in self.scope])

    def __str__(self):
        return "???"

class ASTNodeInitial(ASTNode):
    def __str__(self):
        return self.content()

class ASTNodeFunc(ASTNode):
    def __init__(self, name, scope):
        super().__init__(scope)
        self.name = name

    def __str__(self):
        return f"{self.name} {{\n{tw.indent(self.content(), INDENT)}\n}}"

class ASTNodeLoopStmt(ASTNode):
    def __init__(self, cond: ASTNode, scope):
        super().__init__(scope)
        self.cond = cond

    def __str__(self):
        return f"while({self.cond}) {{\n{tw.indent(self.content(), INDENT)}\n}}"

class ASTNodeIfStmt(ASTNode):
    def __init__(self, cond: ASTNode, scope):
        super().__init__(scope)
        self.cond = cond

    def __str__(self):
        return f"if({self.cond}) {{\n{tw.indent(self.content(), INDENT)}\n}}"

class ASTNodeExpression(ASTNode):
    def __init__(self, expr: str):
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
    def __init__(self, inst, **regs):
        assert type(inst) in {syntax.InstRelJumpConditional, syntax.InstRelJump}
        self.inst = inst
        self.regs = regs

    def __str__(self):
        if type(self.inst) == syntax.InstRelJump:
            return "true"
        else:
            if self.inst.cond == "C":
                return "A >= 0"
            elif self.inst.cond == "NC":
                return "A < 0"
            elif self.inst.cond == "Z":
                return "A != 0"
            elif self.inst.cond == "NZ":
                return "A == 0"
            else:
                raise Exeption("unknown condition")
            return str(self.inst)

def make_scope_for_func(content, regmap):
    scope = []
    for inst, _ in content:
        if type(inst) is not dict:
            expr = inst.dry_run(regmap)
            if expr:
                node = ASTNodeExpression(expr)
                scope.append(node)
        else:
            assert "type" in inst
            assert inst["type"].upper() in ("IF", "LOOP")
            inner_scope = make_scope_for_func(inst["content"], regmap)
            cond = ASTNodeJumpHandler(inst["inst"])
            if inst["type"].upper() == "IF":
                scope.append(ASTNodeIfStmt(cond, inner_scope))
            else:
                scope.append(ASTNodeLoopStmt(cond, inner_scope))
    return scope

def build_ast(explored_tokens):
    scope = []
    regmap = syntax.create_initial_regmap()
    for func, content in explored_tokens.items():
        func_scope = make_scope_for_func(content, regmap)
        scope.append(ASTNodeFunc(name=func, scope=func_scope))
    return ASTNodeInitial(scope=scope)
