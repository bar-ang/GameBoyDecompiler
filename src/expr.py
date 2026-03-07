from __future__ import annotations
import re

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

class Expr:
    def __init__(self, op: TypeBaseExpr,
                a: Expr | None=None,
                b: Expr | None=None,
                *, postpositive: bool=False,
                size_bytes: int=4):
        self.op = op
        self.a = a
        self.b = b
        self._postpositive = postpositive
        self.size_bytes = size_bytes

    @staticmethod
    def make(op: TypeBaseExpr,
             a: TypeBaseExpr | None=None,
             b: TypeBaseExpr | None=None,
             **kwargs) -> Expr:

        p1 = Expr(a) if a is not None else None
        p2 = Expr(b) if b is not None else None

        return Expr(op, p1, p2, **kwargs)

    def op_as_str(self) -> str:
        if type(self.op) == str:
            return self.op

        assert type(self.op) == int
        return f"${self.op:0{self.size_bytes}X}"

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

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        if self.a is not None:
            str_a = str(self.a)
        else:
            str_a = ""

        if self.b is not None:
            str_b = str(self.b)
        else:
            str_b = ""

        regex = r'[A-Za-z0-9&\. ]+'

        if str_a and not re.fullmatch(regex, str_a):
            str_a = f"({str_a})"

        if str_b and not re.fullmatch(regex, str_b):
            str_b = f"({str_b})"

        return f"{str_a}{self.op_as_str()}{str_b}"

    def __eq__(self, other) -> bool:
        if not other:
            return False

        if self.op != other.op:
            return False

        if not (self.a == other.a and self.b == other.b):
            return False

        return True

    def optimize(self) -> Expr:
        opa = None
        opb = None

        if self.a:
            opa = self.a.optimize()

        if self.b:
            opb = self.b.optimize()

        try:
            if opa and opb and isinstance(opa.op, int) and isinstance(opb.op, int):
                return Expr(action_binary[self.op](opa.op, opb.op))
            elif opa and isinstance(opa.op, int) and not opb:
                return Expr(action_unary[self.op](opa.op))
            elif opb and isinstance(opb.op, int) and not opa:
                return Expr(action_unary[self.op](opb.op))
        except KeyError:
            pass

        return Expr(self.op, opa, opb)

def main() -> int:
    a = Expr("a")
    b = Expr("b")
    c = Expr(0xbec)
    t = Expr("+", a, b)
    t2 = Expr("*", c, t)

    print(a)
    print(b)
    print(c)

    print(t)
    print(t2)

    print(Expr.make("++", 5))


    print("optimization")
    ex = Expr(5)
    for i in range(10, 17):
        ex = Expr("+", ex, Expr(i))

    print(f"{ex} --> {ex.optimize()}")

    xxor = Expr.make("^", 9, 9)
    print(f"{xxor} --> {xxor.optimize()}")
    xxor = Expr("^", Expr("foo"), Expr("foo"))
    print(f"{xxor} --> {xxor.optimize()}")
    return 0

if __name__ == "__main__":
    main()

