from expr import Expr
from lr35902dis import lr35902 as disassembler

class ASTNode:
    def __init__(self, op, scope=[]):
        self.op = op
        self.scope = scope

def astBuilder(explored_tokens):
    pass


if __name__ == "__main__":
    ast = AST()
    code = [
        0,                # NOP
        0,                # NOP
        0,                # NOP
        0x3E, 0x99,       # LD A, 123
        0xEA, 0xAB, 0xCD, # LD ($ABCD), A
        0x5F,             # LD E, A
        0x3C,             # INC A
        0xF5,             # PUSH AF
        0xEA, 0xDE, 0xAD, # LD ($DEAD), A
        0xFA, 0xAB, 0xCD, # LD A, ($ABCD)
        0xEA, 0x98, 0x76, # LD ($9876), A
        0xBB,             # CP E
        0x28, 1,          # JR Z, 1
        0x3C,             # INC A
        0xEA, 0x45, 0x45, # LD ($4545), A

    ]

    line = 0
    while code:
        line += 1
        code = ast.step(code)
        print(f"{line}. " + "  ##\t".join([f"{k}: {v}" for k, v in ast._data.items() if k != v]))
    print("\n-------------\n")
    print(ast.decompile())
