import re

class Expr:
    def __init__(self, op: str, a, b=None, *, postpositive=False):
        assert type(a) in (Expr, str), type(a)
        assert b is None or type(b) in (Expr, str), type(b)
        self.op = op
        self.a = a
        self.b = b
        self._postpositive = postpositive

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        regex = r'[A-Za-z0-9&\.]+'
        if type(self.a) == str:
            a_str = self.a
        else:
            a_str = self.a.__str__()

        if not re.fullmatch(regex, a_str):
            a_str = f"({a_str})"

        if self.b is None:
            return f"{self.op}{a_str}"if not self._postpositive else f"{a_str}{self.op}"

        if type(self.b) == str:
            b_str = self.b
        else:
            b_str = self.b.__str__()

        if not re.fullmatch(regex, b_str):
            b_str = f"({b_str})"

        return f"{a_str}{self.op}{b_str}" if not self._postpositive else f"{a_str}{b_str}{self.op}"

