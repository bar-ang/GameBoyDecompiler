import re
from opcodes import *
from lr35902dis import lr35902 as disassembler

class AST:

    REGS = ["A", "B", "C", "D", "E", "F", "H", "L", "PC", "SP"]

    def __init__(self, **initial_data):
        self._data = {r : r for r in self.REGS}
        self._data.update(initial_data)

    def get_data(self, reg):
        if reg not in self._data and reg in ("BC", "DE", "AF", "HL"):
            d1 = self._data.get(reg[0], "??" + reg[0] + "??")
            d2 = self._data.get(reg[1], "??" + reg[1] + "??")

            return Expr("@", d1, d2)
        return self._data.get(reg, "??" + reg + "??")

    @property
    def rA(self):
        return self._data.get("A", "!?A!?")

    def step(self, code):
        opcode = code[0]
        data = self._data

        if opcode == 0x76: # HALT
            return code[1:]

        if opcode >= 0x80 and opcode <= 0xC0:
            # most 8-bit arithmatic commands have opcodes $80-$bf
            # with register ordered: B, C, D, E, H, L, (HL), A
            # all codes in this range do not take constant values
            # therefore they're 1-byte length each.
            n_bytes = 1
            reg_order = ['B', 'C', 'D', 'E', 'H', 'L', "[HL]", 'A']
            reg = reg_order[opcode & 7]
            if opcode & 7 == 6: # has memory access: op a, (HL)
                b = Expr("*", self.get_data("HL"))
            else:
                b = self.get_data(reg)

            if opcode & 0xF0 == 0x80:
                if opcode & 0xF < 8:
                    # It's ADD cmd
                    data["A"] = Expr("+", self.rA, b)
                else:
                    # It's ADC cmd
                    data["A"] = Expr("+`", self.rA, b)
            elif opcode & 0xF0 == 0x90:
                if opcode & 0xF < 8:
                    # It's SUB cmd
                    data["A"] = Expr("-", self.rA, b)
                else:
                    # It's SBC cmd
                    data["A"] = Expr("-`", self.rA, b)
            elif opcode & 0xF0 == 0xA0:
                if opcode & 0xF < 8:
                    # It's AND cmd
                    data["A"] = Expr("&", self.rA, b)
                else:
                    # It's XOR cmd
                    data["A"] = Expr("^", self.rA, b)
            elif opcode & 0xF0 == 0xB0:
                if opcode & 0xF < 8:
                    # It's OR cmd
                    data["A"] = Expr("|", self.rA, b)
                else:
                    # It's CP cmd
                    data["A"] = Expr("==", self.rA, b)
            else:
                raise Exception(f"opcode considered as 8-bit arithmatic, but failed to process: {opcode}")
        elif opcode >= 0x40 and opcode <= 0x80:
            # most 8-bit load commands have opcodes $40-$7f
            # lower nybble decides src register in order same as arithmatic commands
            # upper nybble decides dst register in order.
            # opcode 0x76 is exceptional: HALT - must make sure it won't reach this flow
            # all codes in this range do not take constant values
            # therefore they're 1-byte length each.
            n_bytes = 1
            reg_order = ['B', 'C', 'D', 'E', 'H', 'L', "[HL]", 'A']
            reg = reg_order[opcode & 7]

            if opcode & 7 == 6: # has memory access: op a, (HL)
                b = Expr("*", self.get_data("HL"))
            else:
                b = self.get_data(reg)

            src = opcode & 7
            dest = (opcode & 1) | ((opcode & 0x30) >> 3)
            data[reg_order[dest]] = data[reg_order[src]]

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
        regex = r'[A-Za-z0-9&\.]+'
        if type(self.a) == str:
            a_str = self.a
        else:
            a_str = self.a.__str__()

        if not re.fullmatch(regex, a_str):
            a_str = f"({a_str})"

        if self.b is None:
            return f"{self.op}{a_str}"

        if type(self.b) == str:
            b_str = self.b
        else:
            b_str = self.b.__str__()

        if not re.fullmatch(regex, b_str):
            b_str = f"({b_str})"

        return f"{a_str}{self.op}{b_str}"


if __name__ == "__main__":
    ast = AST()
    res = ast.process_all([0xA5, 0x86, 0xA0, 0x88, 0x5F, 0x93])
    print("\n".join([f"{k} : {v}" for k, v in ast._data.items()]))
