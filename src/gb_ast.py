import textwrap as tw
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

class ASTNodeText(ASTNode):
    def __init__(self, text: str):
        self.text = text
        super().__init__(scope=[])

    def __str__(self):
        return self.text

def make_scope_for_func(content):
    scope = []
    for inst, _ in content:
        if type(inst) is not dict:
            scope.append(ASTNodeText(str(inst)))
        else:
            assert "type" in inst
            assert inst["type"].upper() in ("IF", "LOOP")
            inner_scope = make_scope_for_func(inst["content"])
            cond = ASTNodeText(str(inst["inst"]))
            if inst["type"].upper() == "IF":
                scope.append(ASTNodeIfStmt(cond, inner_scope))
            else:
                scope.append(ASTNodeLoopStmt(cond, inner_scope))
    return scope

def build_ast(explored_tokens):
    scope = []
    for func, content in explored_tokens.items():
        scope.append(ASTNodeFunc(name=func, scope=make_scope_for_func(content)))
    return ASTNodeInitial(scope=scope)
