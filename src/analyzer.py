import re
from opcodes import *
from lr35902dis import lr35902 as disassembler

class AST:

    REGS = ["A", "B", "C", "D", "E", "F", "H", "L", "PC", "SP"]

    def __init__(self, **initial_data):
        self._data = {r : r for r in self.REGS}
        self._data.update(initial_data)
        self._gen_code = []
        self._gen_code_line = []

    def get_data(self, reg):
        if reg not in self._data and reg in ("BC", "DE", "AF", "HL"):
            d1 = self._data.get(reg[0], "??" + reg[0] + "??")
            d2 = self._data.get(reg[1], "??" + reg[1] + "??")

            return Expr(".", d1, d2)
        return self._data.get(reg, "??" + reg + "??")

    def decompile(self):
        gen_code = self._gen_code
        if self._gen_code_line:
            gen_code.append("".join(self._gen_code_line))
        return "\n".join(gen_code)

    def write_code(self, code, break_line=True):
        self._gen_code_line.append(code)
        if break_line:
            self._gen_code.append("".join(self._gen_code_line))
            self._gen_code_line = []

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
                    expr = Expr("-", self.rA, b)
                    self.write_code(f"if {expr}", break_line=False)
            else:
                raise Exception(f"opcode considered as 8-bit arithmatic, but failed to process: {opcode}")
        elif opcode & 0xF0 in {0x20, 0x30} and opcode & 7 == 0:
            # these are the conditional JR commands
            n_bytes = 2
            offset = code[1]
            if opcode == 0x20: # NZ
                self.write_code(" != 0 then:")
            elif opcode == 0x30: # NC
                self.write_code(" >= 0 then:")
            elif opcode == 0x21: # Z
                self.write_code(" == 0 then:")
            else:                # C
                self.write_code(" < 0 then:")
        elif opcode >= 0x40 and opcode <= 0x80:
            assert opcode != 0x76
            # most 8-bit load commands have opcodes $40-$7f
            # lower nybble decides src register in order same as arithmatic commands
            # upper nybble decides dst register in order.
            # opcode 0x76 is exceptional: HALT - must make sure it won't reach this flow
            # all codes in this range do not take constant values
            # therefore they're 1-byte length each.
            n_bytes = 1
            reg_order = ['B', 'C', 'D', 'E', 'H', 'L', "[HL]", 'A']

            src = opcode & 7
            dst = ((opcode & 8) | (opcode & 0x30)) >> 3
            if opcode & 7 == 6: # read from memory: ld r, (HL)
                self.write_code(f"{data[reg_order[dst]]} := {Expr("*", self.get_data("HL"))}")
            elif opcode >= 0x70 and opcode < 0x78: # write to memory: ld (HL), r
                self.write_code(f"{Expr("*", self.get_data("HL"))} := {Expr("*", self.get_data("HL"))}")
            else:
                data[reg_order[dst]] = data[reg_order[src]]
        elif opcode == 0xEA: # LD (a16),A
            n_bytes = 3
            n = code[2] | (code[1] << 8)
            self.write_code(f"*{n:04X} := {self.rA}")
            data[f"*{n:04X}"] = self.rA
        elif opcode == 0xFA: # LD A,(a16)
            n_bytes = 3
            n = code[2] | (code[1] << 8)
            data["A"] = Expr("*", f"{n:04X}")
        elif opcode >= 0xC0 and opcode & 7 == 6:
            # these are all 2-byte commands operating on reg A
            n_bytes = 2
            op_order = ["+", "+`", "-", "-`", "&", "^", "|", "=="]
            op = ((opcode & 8) | (opcode & 0x30)) >> 3
            data["A"] = Expr(op_order[op], self.rA, f"{code[1]:02X}")
        elif opcode < 0x40 and opcode & 7 in {4, 5}:
            # these are all 1-byte commands with the standard reg order
            # INC and DEC.
            n_bytes = 1
            reg_order = ['B', 'C', 'D', 'E', 'H', 'L', "[HL]", 'A']
            op_order = ["++", "--"]

            reg = ((opcode & 8) | (opcode & 0x30)) >> 3
            op = opcode & 3
            data[reg_order[reg]] = Expr(op_order[op], data[reg_order[reg]], postpositive=True)
        elif opcode < 0x40 and opcode & 7 == 6:
            # 2-bytes LD commands
            n_bytes = 2
            reg_order = ['B', 'C', 'D', 'E', 'H', 'L', "[HL]", 'A']

            reg = ((opcode & 8) | (opcode & 0x30)) >> 3
            if reg != 6: # reg is not [HL]
                data[reg_order[reg]] = f"{code[1]:02X}"
            else:
                self.write_code(f"{self.get_data("HL")} := {code[1]:02X}")
        elif opcode < 0x40 and opcode & 7 == 2:
            # these are LD commands that involve 16-bit regs
            n_bytes = 1
            reg_order = ["BC", "DE", "HL+", "HL-"]
            reg = (opcode & 0x30) >> 4
            if opcode & 0xf == 2: # store
                self.write_code(f"{self.get_data(reg_order[reg][:2])} := {self.rA}")
            else: # load
                data["A"] = Expr("*", self.get_data(reg_order[reg][:2]))

            if reg == 2:
                data["HL"] = Expr("++", self.get_data("HL"), postpositive=True)
            elif reg == 3:
                data["HL"] = Expr("--", self.get_data("HL"), postpositive=True)

        elif opcode == 0xCB:
            # for now, we won't identify the command exactly
            opcode = code[1]
            n_bytes = 3
            reg_order = ['B', 'C', 'D', 'E', 'H', 'L', "[HL]", 'A']

            reg = opcode & 7
            beta =  ((opcode & 8) | (opcode & 0xF)) >> 3
            data[reg_order[reg]] = Expr(f"β{beta}", self.get_data(reg_order[reg]))
        elif opcode == 0xE0: # LDH (addr), A
            n_bytes = 2
            deref = Expr("*", self.get_data(opcode[1]))
            self.write_code(f"{deref} := {self.rA}")
        elif opcode == 0xF0: # LDH A, (addr)
            n_bytes = 2
            data["A"] = Expr("*", f"FF{code[1]:02X}")
        elif opcode == 0xE2: # LD (C), A
            deref = Expr("*", Expr("+", "FF00", self.get_data("C")))
            self.write_code(f"{deref} := {self.rA}")
            n_bytes = 2
        elif opcode == 0xF2: # LD A, (C)
            n_bytes = 2
            data["A"] = Expr("*", Expr("+", "FF00", self.get_data("C")))

        else:
            dis = ""
            n_bytes = 0
            while not dis:
                n_bytes += 1
                dis = disassembler.disasm(bytes(code[:n_bytes]), 0)
                if n_bytes > 3:
                    str_code = " ".join(f"{c:02X}" for c in code[:n_bytes])
                    raise Exception(f"Unknown instruction: {str_code}")
            self.write_code(f"@ {dis}")
            print(f"unhandeled {n_bytes}-bytes opcode '{opcode:02X}'. Disassembled as '{dis}'.")

        return code[n_bytes:]

    def process_all(self, code):
        while len(code) > 0:
            code = self.step(code)


class Expr:
    def __init__(self, op, a, b=None, *, postpositive=False):
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
