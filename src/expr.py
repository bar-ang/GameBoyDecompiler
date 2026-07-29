from __future__ import annotations
import re
from abc import ABC

TypeBaseExpr = int | str

action_binary = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "^": lambda a, b: a ^ b,
    ".": lambda a, b: 256*a + b
}

action_unary = {
    ">>1": lambda a: a >> 1,
    "~":   lambda a: ~a,
}

class Expr(ABC):
    def optimize(self) -> Expr:
        pass

class OperatorExpr(Expr, ABC):
    def __init__(self, op: str,
                 a: Expr | None = None,
                 b: Expr | None = None,
                 *, postpositive: bool=False):
        self.op = op
        self.a = a or PrimitiveNone()
        self.b = b or PrimitiveNone()
        self._postpositive = postpositive

    @property
    def high(self) -> Expr:
        if isinstance(self.op, int):
            return Expr(self.op >> 8)
        return Expr("HIGH", self)

    @property
    def low(self) -> Expr:
        if isinstance(self.op, int):
            return Expr(self.op & 0xff)
        return Expr("LOW", self)

    def split(self) -> tuple[Expr, Expr]:
        return self.high, self.low

    def optimize(self) -> Expr:
        return OperatorExpr(self.op, self.a.optimize(), self.b.optimize())

    def __str__(self):
        regex = r'[A-Za-z0-9&\. ]+'
        str_a = f"{self.a}"
        str_b = f"{self.b}"

        if str_a and not re.fullmatch(regex, str_a):
            str_a = f"({str_a})"

        if str_b and not re.fullmatch(regex, str_b):
            str_b = f"({str_b})"

        if self._postpositive:
            return f"{self.op}{str_a}{str_b}"

        return f"{str_a}{self.op}{str_b}"


class ArithExpr(OperatorExpr):
    def __init__(self, op: str,
                 a: Expr,
                 b: Expr | None = None,
                 associative: bool = False,
                 commutative: bool = False,
                 inversible: bool = False,
                 neutral_obj: Primitive | None = None,
                 *, postpositive: bool=False):
        super().__init__(op, a, b, postpositive=postpositive)
        self.associative = associative
        self.commutative = commutative
        self.inversible = inversible
        self.neutral_obj = neutral_obj

    def optimize(self) -> Expr:
        pass

class ComparativeExpr(OperatorExpr):
    def __init__(self, op: str,
                 a: Expr,
                 b: Expr,
                 *, postpositive: bool=False):
        super().__init__(op, a, b, postpositive=postpositive)


#    @staticmethod
#    def make(op: TypeBaseExpr,
#             a: TypeBaseExpr | None=None,
#             b: TypeBaseExpr | None=None,
#             **kwargs) -> Expr:

#        p1 = Expr(a) if a is not None else None
#        p2 = Expr(b) if b is not None else None

#        return Expr(op, p1, p2, **kwargs)

#    def op_as_str(self) -> str:
#        if type(self.op) == str:
#            return self.op

#        assert type(self.op) == int
#        return f"${self.op:0{self.size_bytes}X}"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        if not other:
            return False

        if self.op != other.op:
            return False

        if not (self.a == other.a and self.b == other.b):
            return False

        return True

    def optimize(self) -> Expr:
        pass


class PrimitiveExpr(Expr, ABC):
    def __init__(self, data: str | int | None = None):
        self.data = data

    def optimize(self):
        pass

    def __eq__(self, other):
        return self.data == other.data

class PrimitiveNone(PrimitiveExpr):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return ""

    def optimize(self):
        return PrimitiveNone()

class PrimitiveConst(PrimitiveExpr):
    def __init__(self, const: int):
        super().__init__(const)

    @property
    def const(self):
        assert isinstance(self.data, int)
        return self.data

    def __str__(self):
        return f"${self.const:x}"

    def optimize(self):
        return PrimitiveConst(self.const)

class PrimitiveVar(PrimitiveExpr):
    def __init__(self, var: str):
        super().__init__(var)

    @property
    def var(self):
        assert isinstance(self.data, str)
        return self.data

    def optimize(self):
        return PrimitiveVar(self.var)

    def __str__(self):
        return self.var

class PrimitivePointer(PrimitiveExpr):
    def __init__(self, pointer: int, size_bytes: int = 4):
        super().__init__(pointer)
        self.size_bytes = size_bytes

    @property
    def pointer(self):
        assert isinstance(self.data, int)
        return self.data

    def optimize(self):
        return PrimitivePointer(self.pointer, self.size_bytes)

    def __str__(self):
        return f"${self.pointer:0{self.size_bytes}X}"

def main() -> int:
    a = PrimitiveVar("a")
    b = PrimitiveVar("b")
    c = PrimitiveConst(0xbec)
    p = PrimitivePointer(0xe)

    t = ArithExpr("+", a, b, True, True, True, PrimitiveConst(0))
    t2 = ArithExpr("*", a, b, True, True, True, PrimitiveConst(1))

    print(a)
    print(b)
    print(c)
    print(p)

    print(t)
    print(t2)

    print(ArithExpr("++", PrimitiveConst(5)))
    print(ArithExpr("++", PrimitiveConst(5), postpositive=True))


    print("optimization")
    ex = PrimitiveConst(5)
    for i in range(10, 17):
        ex = ArithExpr("+", ex, PrimitiveConst(i), True, True, True, PrimitiveConst(0))

    print(f"{ex} --> {ex.optimize()}")

    xxor = ArithExpr("^", PrimitiveConst(9), PrimitiveConst(9))
    print(f"{xxor} --> {xxor.optimize()}")
    xxor2 = ArithExpr("^", PrimitiveVar("foo"), PrimitiveVar("foo"))
    print(f"{xxor2} --> {xxor2.optimize()}")

    assert a == PrimitiveVar("a")
    assert t2 == ArithExpr("*", c, t, True, True, True, PrimitiveConst(1))
    assert PrimitiveConst(0) == xxor.optimize()
    assert ArithExpr("^", PrimitiveVar("foo"), PrimitiveVar("foo")) == xxor2.optimize()

    return 0

if __name__ == "__main__":
    main()

