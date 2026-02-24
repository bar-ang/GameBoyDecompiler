from __future__ import annotations
import re

TypeBaseExpr = int | str


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

    def op_as_str(self):
        if type(self.op) == str:
            return self.op

        assert type(self.op) == int
        return f"${self.op:0{self.size_bytes}X}"

    def __repr__(self):
        return self.__str__()

    def __str__(self):
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


def main():
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

    print(Expr("++", 5))

    return 0

if __name__ == "__main__":
    main()

