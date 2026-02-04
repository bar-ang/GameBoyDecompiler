from expr import Expr
from lr35902dis import lr35902 as disassembler

class AST:

    REGS = ["A", "B", "C", "D", "E", "F", "H", "L", "PC", "SP"]

    def __init__(self, code=None, initial_scope=0, scope_data={}, endianness="little", strict=True, pc_start=0, **initial_data):
        assert endianness in ("big", "little")

        self._data = {r : r for r in self.REGS}
        self._data.update(initial_data)
        self._gen_code = []
        self._endianness = 0 if endianness == "little" else 1
        self._strict = strict
        self._pc = pc_start
        self._scope_data = scope_data.copy()
        self._scope_level = initial_scope

        if code is not None:
            self.process_all(code)

    def get_data(self, reg):
        if reg not in self._data and reg in ("BC", "DE", "AF", "HL"):
            if not self._strict:
                d1 = self._data.get(reg[0], "??" + reg[0] + "??")
                d2 = self._data.get(reg[1], "??" + reg[1] + "??")
            else:
                d1 = self._data[reg[0]]
                d2 = self._data[reg[1]]

            return Expr(".", d1, d2)

        if not self._strict:
            return self._data.get(reg, "??" + reg + "??")
        else:
            return self._data[reg]

    def decompile(self, tabsize=4):
        return "\n".join([" " * tabsize * scope + c for c, scope in self._gen_code])

    def write_code(self, code):
        self._gen_code.append((code, self._scope_level))

    def enter_scope(self):
        self.write_code("{")
        self._scope_level += 1

    def exit_scope(self):
        assert self._scope_level > 0
        self._scope_level -= 1
        self.write_code("}")

    @property
    def rA(self):
        return self._data.get("A", "!?A!?")

    @property
    def pc(self):
        return self._pc

    def step(self, code):
        opcode = code[0]
        data = self._data

        if self.pc in self._scope_data["closes"]:
            self.exit_scope()
        if self.pc in self._scope_data["opens"]:
            self.enter_scope()

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
                    data["F"] = Expr("-", self.rA, b)
            else:
                raise Exception(f"opcode considered as 8-bit arithmatic, but failed to process: {opcode}")
        elif opcode & 0xF0 in {0x20, 0x30} and opcode & 7 == 0:
            # these are the conditional JR commands
            n_bytes = 2
            offset = code[1]
            todo = f"skip {offset} line"
            if offset == 0:
                todo = "continue regularly"
            elif offset < 0:
                todo = f"go back {-offset} lines"
            if opcode == 0x20: # NZ
                self.write_code(f"if {self.rA} != 0 then {todo}")
            elif opcode == 0x30: # NC
                self.write_code(f"if {self.rA} >= 0 then {todo}")
            elif opcode == 0x21: # Z
                self.write_code(f"if {self.rA} == 0 then {todo}")
            else:                # C
                self.write_code(f"if {self.rA} < 0 then {todo}")
        elif opcode & 0xF0 in {0xC0, 0xD0} and opcode & 7 == 2:
            # these are the conditional JP commands
            n_bytes = 3
            offset = code[1 + self._endianness] | (code[2 - self._endianness] << 8)
            todo = f"goto line {offset}"
            if opcode == 0x20: # NZ
                self.write_code(f"if {self.rA} != 0 then {todo}")
            elif opcode == 0x30: # NC
                self.write_code(f"if {self.rA} >= 0 then {todo}")
            elif opcode == 0x21: # Z
                self.write_code(f"if {self.rA} == 0 then {todo}")
            else:                # C
                self.write_code(f"if {self.rA} < 0 then {todo}")
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
            n = code[1 + self._endianness] | (code[2 - self._endianness] << 8)
            self.write_code(f"*{n:04X} := {self.rA}")
            data[f"*{n:04X}"] = self.rA
        elif opcode == 0xFA: # LD A,(a16)
            n_bytes = 3
            n = code[1 + self._endianness] | (code[2 - self._endianness] << 8)
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
            if reg_order[reg] != "[HL]":
                data[reg_order[reg]] = Expr(op_order[op], data[reg_order[reg]], postpositive=True)
            else:
                data[self.get_data("HL")] = Expr(op_order[op], Expr("*", self.get_data("HL")))

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
            if reg_order[reg] != "[HL]":
                data[reg_order[reg]] = Expr(f"β{beta}", self.get_data(reg_order[reg]))
            else:
                data[self.get_data("HL")] = Expr(f"β{beta}", Expr("*", self.get_data("HL")))
        elif opcode < 0x40 and opcode & 0xF == 1:
            # 16 bits immediate value LD commands
            n_bytes = 3
            reg_order = ["BC", "DE", "HL", "SP"]
            reg = reg_order[opcode >> 4]
            if reg != "SP":
                data[reg[0]] = f"{code[2 - self._endianness]:02X}"
                data[reg[1]] = f"{code[1 + self._endianness]:02X}"
            else:
                value = (code[2 - self._endianness] << 8) | code[1 + self._endianness]
                data["SP"] = f"{value:04X}"
        elif opcode < 0x40 and opcode & 0x7 == 3:
            # 16 bits INC and DEC
            print(f"{opcode:02X}: command is not properly implemented. expects bugs.")
            n_bytes = 1
            reg_order = ["BC", "DE", "HL", "SP"]
            reg = reg_order[opcode >> 4]
            sign = "++" if opcode & 0xF == 3 else "--"
            if reg != "SP":
                # TODO: this doesn't take care of overflow!!!!!!!!!!!!!
                data[reg[1]] = Expr(sign, data[reg[1]], postpositive=True)
            else:
                data["SP"] = Expr(sign, data["SP"], postpositive=True)
        elif opcode >= 0xC0 and opcode & 0xF == 1:
            # POP commands
            print(f"{opcode:02X}: command is not properly implemented. expects bugs.")
            n_bytes = 1
            reg_order = ["BC", "DE", "HL", "AF"]
            reg = reg_order[(opcode & 0x30) >> 4]
            data["SP"] = Expr("-2", data["SP"], postpositive=True)
            data[reg] = ":)"
        elif opcode >= 0xC0 and opcode & 0xF == 5:
            # PUSH commands
            print(f"{opcode:02X}: command is not properly implemented. expects bugs.")
            n_bytes = 1
            reg_order = ["BC", "DE", "HL", "AF"]
            reg = reg_order[(opcode & 0x30) >> 4]
            data["SP"] = Expr("+2", data["SP"], postpositive=True)
        elif opcode == 0xE0: # LDH (addr), A
            n_bytes = 2
            deref = f"*FF{code[1]:02X}"
            data[deref] = self.rA
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
        elif opcode == 0x00:
            # NOP command, do nothing
            n_bytes = 1
        elif opcode == 0xC9:
            # uncoditional RET commands, already handled by the explorer
            n_bytes = 1
        elif opcode == 0xCD:
            # unconditional CALL
            n_bytes = 3
            n = code[1 + self._endianness] | (code[2 - self._endianness] << 8)
            self.write_code(f"fun_{n:04X}()")
        else:
            dis = ""
            n_bytes = 0
            while not dis:
                n_bytes += 1
                dis = disassembler.disasm(bytes(code[:n_bytes]), 0)
                if n_bytes > 3:
                    str_code = " ".join(f"{c:02X}" for c in code[:n_bytes])
                    raise Exception(f"Unknown instruction: {str_code}")
            self.write_code(f"{dis}()\t\t// native asm op")

        self._pc += n_bytes
        return code[n_bytes:]

    def process_all(self, code):
        while len(code) > 0:
            code = self.step(code)


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
