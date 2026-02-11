from expr import Expr
from lr35902dis import lr35902 as disassembler

class ASTNode:
    def __init__(self, scope):
        self.scope = scope

    def content(self, depth=1):
        return "\n".join(["\t"*depth + str(c) for c in self.scope])

    def __str__(self):
        return "???"

class ASTNodeInitial(ASTNode):
    def __str__(self):
        return self.content(0)

class ASTNodeFunc(ASTNode):
    def __init__(self, name, scope):
        super().__init__(scope)
        self.name = name

    def __str__(self):
        return f"{self.name} {{\n{self.content()}\n}}"

class ASTNodeLoop(ASTNode):
    def __init__(self, cond, scope):
        super().__init__(scope)
        self.cond = cond

    def __str__(self):
        return f"while({self.cond}) {{\n{self.content()}\n}}"


class ASTNodeCondition(ASTNode):
    def __init__(self, cond, scope):
        super().__init__(scope)
        self.cond = cond

    def __str__(self):
        return f"if({self.cond}) {{\n{self.content()}\n}}"

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
            if inst["type"].upper() == "IF":
                scope.append(ASTNodeCondition(inst["inst"], inner_scope))
            else:
                scope.append(ASTNodeLoop(inst["inst"], inner_scope))
    return scope

def build_ast(explored_tokens):
    scope = []
    for func, content in explored_tokens.items():
        scope.append(ASTNodeFunc(name=func, scope=make_scope_for_func(content)))
    return ASTNodeInitial(scope=scope)
