from opcodes import *
from lr35902dis import lr35902 as disassembler

class AST:

    REGS = ["A", "B", "C", "D", "E", "F", "H", "L", "PC", "SP"]

    def __init__(self, **initial_data):
        self._data = {r : r for r in self.REGS}
        self._data.update(initial_data)

    def get_data(self, reg):
        return self._data.get(reg, "??" + reg + "??")

    @property
    def rA(self):
        return self._data.get("A", "!?A!?")

    def step(self, code):
        opcode = code[0]
        data = self._data

        if opcode >= 0x80 and opcode <= 0xC0:
            # most 8-bit arithmatic commands have opcodes $80-$bf
            # with register ordered: B, C, D, E, H, L, (HL), A
            # all codes in this range do not take constant values
            # therefore they're 1-byte length each.
            n_bytes = 1
            reg_order = ['B', 'C', 'D', 'E', 'H', 'L', "#OOPS!#", 'A']
            if opcode & 0xF0 == 0x80:
                reg = reg_order[opcode & 7]
                if opcode & 0xF < 8:
                    # It's ADD cmd
                    data["A"] = Expr("+", self.rA, self.get_data(reg))
                else:
                    # It's ADC cmd
                    data["A"] = Expr("+`", self.rA, self.get_data(reg))
            elif opcode & 0xF0 == 0x90:
                reg = reg_order[opcode & 7]
                if opcode & 0xF < 8:
                    # It's SUB cmd
                    data["A"] = Expr("-", self.rA, self.get_data(reg))
                else:
                    # It's SBC cmd
                    data["A"] = Expr("-`", self.rA, self.get_data(reg))
            elif opcode & 0xF0 == 0xA0:
                reg = reg_order[opcode & 7]
                if opcode & 0xF < 8:
                    # It's AND cmd
                    data["A"] = Expr("&", self.rA, self.get_data(reg))
                else:
                    # It's XOR cmd
                    data["A"] = Expr("^", self.rA, self.get_data(reg))
            elif opcode & 0xF0 == 0xB0:
                reg = reg_order[opcode & 7]
                if opcode & 0xF < 8:
                    # It's OR cmd
                    data["A"] = Expr("|", self.rA, self.get_data(reg))
                else:
                    # It's CP cmd
                    data["A"] = Expr("==", self.rA, self.get_data(reg))
            else:
                raise Exception(f"could not handle opcode {opcode}")

        return code[n_bytes:]

    def process_all(self, code):
        while len(code) > 0:
            code = self.step(code)


class Expr:
    def __init__(self, op, a, b=None):
        self.op = op
        self.a = a
        self.b = b

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.b is None:
            return f"{self.op}({self.a})"
        return f"({self.a}){self.op}({self.b})"


if __name__ == "__main__":
    ast = AST()
    res = ast.process_all([0xA5, 0xA0, 0x88])
    print(ast.rA)
