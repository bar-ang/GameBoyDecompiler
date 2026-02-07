from abc import ABC, abstractmethod
import sys

instructions = []

DIRECT_OP = "[HL]"

REG_ORDER   = ['B', 'C', 'D', 'E', 'H', 'L', DIRECT_OP, 'A']
REG16_ORDER = ["BC", "DE", "HL+", "HL-"]
OP_ORDER    = ["ADD", "ADC", "SUB", "SBC", "AND", "XOR", "OR", "CP"]
COND_ORDER  = ["NZ", "Z", "NC", "C"]
INC_ORDER   = ["INC", "DEC"]


def attach_two_bytes(bts, endianness=0):
    return bts[endianness] | (bts[1 - endianness] << 8)

def consume(code, endianness="little"):
    assert endianness in ("big", "little")
    endianness = 0 if endianness == "little" else 1

    opcode = code[0]

    if opcode == 0x76:
        return InstControl("HALT"), code[1:]

    elif opcode == 0x07:
        return InstALU("RLCA"), code[1:]

    elif opcode == 0x17:
        return InstALU("RLA"), code[1:]

    elif opcode == 0x0F:
        return InstALU("RRCA"), code[1:]

    elif opcode == 0x1F:
        return InstALU("RRA"), code[1:]

    elif opcode == 0x00:
        return InstControl("NOP"), code[1:]

    elif opcode == 0x10:
        return InstControl("STOP"), code[2:]

    elif opcode == 0x27:
        return InstALU("DAA"), code[1:]

    elif opcode == 0x37:
        return InstALU("SCD"), code[1:]

    elif opcode == 0x2F:
        return InstALU("CPL"), code[1:]

    elif opcode == 0x3F:
        return InstALU("CCF"), code[1:]

    elif opcode == 0xF3:
        return InstControl("DI"), code[1:]

    elif opcode == 0xFB:
        return InstControl("EI"), code[1:]

    elif opcode >= 0x80 and opcode < 0xC0:
        # most 8-bit arithmatic commands have opcodes $80-$bf
        # with register ordered: B, C, D, E, H, L, (HL), A
        # all codes in this range do not take constant values
        # therefore they're 1-byte length each.
        n_bytes = 1
        op = OP_ORDER[(opcode & 0x38) >> 3]
        if opcode & 7 == 6: # has memory access: op a, (HL)

            return InstALUDirect(op), code[n_bytes:]
        reg = REG_ORDER[opcode & 7]

        return InstALU(op, reg), code[n_bytes:]

    elif opcode & 0xF0 in {0x20, 0x30} and opcode & 7 == 0:
        # these are the conditional JR commands
        n_bytes = 2
        offset = code[1]
        cond = COND_ORDER[(opcode & 0x18) >> 3]

        return InstRelJumpConditional("JR", cond=cond, addr=offset), code[n_bytes:]

    elif opcode & 0xF0 in {0xC0, 0xD0} and opcode & 7 == 2:
        # these are the conditional JP commands
        n_bytes = 3
        pc = attach_two_bytes(code[1:3], endianness)
        cond = COND_ORDER[(opcode & 0x18) >> 3]

        return InstAbsJumpConditional("JP", cond=cond, addr=pc), code[n_bytes:]

    elif opcode == 0xC3:
        # unconditional JP command
        n_bytes = 3
        pc = attach_two_bytes(code[1:3], endianness)

        return InstAbsJump("JP", addr=pc), code[n_bytes:]

    elif opcode == 0x18:
        # unconditional JR command
        n_bytes = 2

        return InstRelJump("JR", addr=code[1]), code[n_bytes:]

    elif opcode >= 0x40 and opcode <= 0x80:
        assert opcode != 0x76, "HALT command should have been handled already"
        # most 8-bit load commands have opcodes $40-$7f
        # lower nybble decides src register in order same as arithmatic commands
        # upper nybble decides dst register in order.
        # opcode 0x76 is exceptional: HALT - must make sure it won't reach this flow
        # all codes in this range do not take constant values
        # therefore they're 1-byte length each.
        n_bytes = 1

        src = opcode & 7
        dst = ((opcode & 8) | (opcode & 0x30)) >> 3
        if opcode & 7 == 6:
            # read from memory: ld r, (HL)
            cmd = InstLoadHLToReg
        elif opcode >= 0x70 and opcode < 0x78:
            # write to memory: ld (HL), r
            cmd = InstLoadRegToHL
        else:
            cmd = InstLoadRegToReg

        return cmd( REG_ORDER[dst], REG_ORDER[src]), code[n_bytes:]

    elif opcode >= 0xC0 and opcode & 7 == 7:
        # RST commands
        val = opcode & 0x38
        return InstReset("RST", imm=val), code[1:]

    elif opcode == 0xEA: # LD (a16),A
        n_bytes = 3
        n = attach_two_bytes(code[1:3], endianness)

        return InstStoreAddr("LD (store)", addr=n), code[n_bytes:]

    elif opcode == 0xFA: # LD A,(a16)
        n_bytes = 3
        n = attach_two_bytes(code[1:3], endianness)

        return InstLoadAddr("LD (load)", addr=n), code[n_bytes:]

    elif opcode >= 0xC0 and opcode & 7 == 6:
        # these are all 2-byte commands operating on reg A
        n_bytes = 2
        op = (opcode & 0x38) >> 3

        return InstALUImmediate(OP_ORDER[op], imm=code[1]), code[n_bytes:]

    elif opcode < 0x40 and opcode & 7 in {4, 5}:
        # these are all 1-byte commands with the standard reg order
        # INC and DEC.
        n_bytes = 1

        reg = ((opcode & 8) | (opcode & 0x30)) >> 3
        op = opcode & 3
        if reg == 6:
            cmd = InstIncDecDirect
        else:
            cmd = InstIncDec

        return cmd(INC_ORDER[op], REG_ORDER[reg]), code[n_bytes:]

    elif opcode < 0x40 and opcode & 7 == 6:
        # 2-bytes LD commands
        n_bytes = 2

        reg = ((opcode & 8) | (opcode & 0x30)) >> 3
        if reg == 6: # reg is [HL]
            cmd = InstLoadDirect
        else:
            cmd = InstLoadImmediate

        return cmd("LD", REG_ORDER[reg], imm=code[1]), code[n_bytes:]

    elif opcode < 0x40 and opcode & 7 == 2:
        # these are LD commands that involve 16-bit regs
        n_bytes = 1

        reg = (opcode & 0x30) >> 4
        if opcode & 0xf == 2: # store
            return InstStore16bit("LD (store)", REG_ORDER[reg]), code[n_bytes:]
        else: # load
            return InstLoad16bit("LD (load)", REG_ORDER[reg]), code[n_bytes:]

    elif opcode == 0xCB:
        #TODO for now, we won't identify the command exactly
        n_bytes = 2

        op = code[1]
        reg = op & 7
        beta =  op >> 3
        if reg == 6:
            return InstCBPrefixDirect(f"β{beta}"), code[n_bytes:]

        return InstCBPrefix(f"β{beta}", REG_ORDER[reg]), code[n_bytes:]

    elif opcode < 0x40 and opcode & 0xF == 1:
        # 16 bits immediate value LD commands
        n_bytes = 3
        reg_order = ["BC", "DE", "HL", "SP"]
        reg = opcode >> 4
        n = attach_two_bytes(code[1:3], endianness)

        return InstLoadImmediate16bit(f"LD", reg_order[reg], imm=n), code[n_bytes:]

    elif opcode < 0x40 and opcode & 0x7 == 3:
        # 16 bits INC and DEC
        n_bytes = 1
        reg_order = ["BC", "DE", "HL", "SP"]
        reg = opcode >> 4
        op = opcode & 1

        return InstIncDec16bit(INC_ORDER[op], reg_order[reg]), code[n_bytes:]

    elif opcode < 0x40 and opcode & 0xF == 9:
        # ADD HL, r16
        n_bytes = 1
        reg_order = ["BC", "DE", "HL", "SP"]
        reg = opcode >> 4

        return InstALU16bit("ADD", reg_order[reg]), code[n_bytes:]

    elif opcode == 0xE8:
        # ADD SP, r8
        n_bytes = 2

        return InstALUregSP("ADD", "SP", f"{code[1]:02x}"), code[n_bytes:]

    elif opcode >= 0xC0 and opcode & 0xF == 1:
        # POP commands
        n_bytes = 1
        reg_order = ["BC", "DE", "HL", "AF"]
        reg = (opcode & 0x30) >> 4

        return InstPop("POP", reg_order[reg]), code[n_bytes:]

    elif opcode >= 0xC0 and opcode & 0xF == 5:
        # PUSH commands
        n_bytes = 1
        reg_order = ["BC", "DE", "HL", "AF"]
        reg = (opcode & 0x30) >> 4

        return InstPush("Push", reg_order[reg]), code[n_bytes:]

    elif opcode == 0xE0:
        # LDH (addr), A
        n_bytes = 2

        return InstHighStore("LDH (store)", code[1]), code[n_bytes:]

    elif opcode == 0xF0:
        # LDH A, (addr)
        n_bytes = 2

        return InstHighStore("LDH (load)", code[1]), code[n_bytes:]

    elif opcode == 0xE2:
        # LD (C), A
        n_bytes = 2

        return InstHighCStore("LDH (C), A"), code[n_bytes:]

    elif opcode == 0xF2:
        # LD A, (C)
        n_bytes = 2

        return InstHighCStore("LDH A, (C)"), code[n_bytes:]

    elif opcode == 0xC9:
        return InstRet("RET"), code[1:]

    elif opcode == 0xD9:
        return InstRet("RETI"), code[1:]

    elif opcode & 0xF0 in {0xC0, 0xD0} and opcode & 7 == 0:
        # Conditional RET
        n_bytes = 1
        cond = COND_ORDER[(opcode & 0x18) >> 3]

        return InstConitionalRet("RET",cond=cond), code[n_bytes:]

    elif opcode == 0xCD:
        # unconditional CALL
        n_bytes = 3
        n = attach_two_bytes(code[1:3], endianness)

        return InstCall("CALL", addr=n), code[n_bytes:]

    elif opcode & 0xF0 in {0xC0, 0xD0} and opcode & 7 == 4:
        # Conditional CALL
        n_bytes = 3
        pc = attach_two_bytes(code[1:3], endianness)
        cond = COND_ORDER[(opcode & 0x18) >> 3]

        return InstConitionalCall("CALL", addr=pc, cond=cond), code[n_bytes:]


    raise Exception(f"Unknown instruction: {opcode:02X}")


class Instruction(ABC):

    def __init__(self, op, regl=None, regr=None, *, imm=0, addr=0, cond=""):
        self.op = op
        self.regl = regl
        self.regr = regr
        self.imm = imm
        self.addr = addr
        self.cond = cond

    def __str__(self):
        return f"[[GENERIC]] {self.op} {self.cond} {self.regl}, {self.regr}, {self.imm:02x}, ({self.addr:04x})"


class InstFamilyOpOnly(Instruction):
    def __init__(self, op):
        return super().__init__(op)

    def __str__(self):
        return f"{self.op}"


class InstFamilySingleReg(Instruction):
    def __init__(self, op, reg="A"):
        return super().__init__(op, reg)

    def __str__(self):
        return f"{self.op} {self.regl}"


class InstFamilyTwoRegs(Instruction):
    def __init__(self, op, regl="A", regr="A"):
        return super().__init__(op, regl, regr)

    def __str__(self):
        return f"{self.op} {self.regl}, {self.regr}"


class InstFamilyRegWithImmediate(Instruction):
    def __init__(self, op, reg="A", imm="0"):
        return super().__init__(op, reg, imm=imm)

    def __str__(self):
        return f"{self.op} {self.regl}, ${self.imm:04x}"


class InstFamilyAddr(Instruction):
    def __init__(self, op, addr):
        return super().__init__(op, addr=addr)

    def __str__(self):
        return f"{self.op} ${self.addr:04x}"


class InstFamilyDirect(Instruction):
    def __init__(self, op, reg):
        return super().__init__(op, reg)

    def __str__(self):
        return f"{self.op} ({self.regl})"


class InstFamilyStoreReg(Instruction):
    def __init__(self, op, regl, regr):
        return super().__init__(op, regl, regr)

    def __str__(self):
        return f"{self.op} ({self.regl}), {self.reg}"


class InstFamilyLoadReg(Instruction):
    def __init__(self, op, regl, regr):
        return super().__init__(op, regl, regr)

    def __str__(self):
        return f"{self.op} {self.regl}, ({self.reg})"


class InstFamilyStoreImm(Instruction):
    def __init__(self, op, regl, imm):
        return super().__init__(op, regl, imm=imm)

    def __str__(self):
        return f"{self.op} ({self.regl}), ${self.imm:02x}"


class InstFamilyLoadImm(Instruction):
    def __init__(self, op, imm, regr):
        return super().__init__(op, regr=regr, imm=m)

    def __str__(self):
        return f"{self.op} (${self.imm:04x}), {self.regr}"


class InstFamilyStoreImm(Instruction):
    def __init__(self, op, reg, imm):
        return super().__init__(op, reg, imm=imm)

    def __str__(self):
        return f"{self.op} {self.regl}, ${self.imm:04x}"


class InstFamilyCondition(Instruction):
    def __init__(self, op, cond, addr=0):
        return super().__init__(op, cond=cond, addr=addr)

    def __str__(self):
        return f"{self.op} {self.cond}, ${self.addr:04x}"



class InstALUregSP(Instruction):
    # NOTE: a rare command (E8h), barely used
    pass


class InstALU(InstFamilyTwoRegs):
    pass


class InstALU16bit(InstFamilyTwoRegs):
    pass


class InstALUDirect(InstFamilyLoadReg):
    pass


class InstALUImmediate(InstFamilyRegWithImmediate):
    pass


class InstIncDec(InstFamilySingleReg):
    pass


class InstIncDecDirect(InstFamilyDirect):
    pass


class InstIncDec16bit(InstFamilySingleReg):
    pass


class InstCBPrefixDirect(InstFamilyDirect):
    pass


class InstCBPrefix(InstFamilySingleReg):
    pass


class InstRelJumpConditional(InstFamilyCondition):
    pass


class InstAbsJumpConditional(InstFamilyCondition):
    pass


class InstRelJump(InstFamilyAddr):
    pass


class InstAbsJump(InstFamilyAddr):
    pass


class InstPush(InstFamilySingleReg):
    pass


class InstPop(InstFamilySingleReg):
    pass


#class InstLoadSPToHL(InstFamilyRegWithImmediate):
    # NOTE: a rare command (F8h), barely used
#    def __str__(self):
#        return f"{self.op} {self.regl}, SP+${self.imm:02x}"


class InstLoadImmediate16bit(InstFamilyRegWithImmediate):
    pass


class InstLoadImmediate(InstFamilyRegWithImmediate):
    pass


class InstLoadDirect(InstFamilyLoadReg):
    pass


class InstLoadRegToReg(InstFamilyTwoRegs):
    pass


class InstLoadRegToHL(InstFamilyStoreReg):
    pass


class InstLoadHLToReg(InstFamilyLoadReg):
    pass


class InstLoadRegToHLI(InstFamilyStoreReg):
    pass


class InstLoadHLIToReg(InstFamilyLoadReg):
    pass


class InstLoad16bit(InstFamilyLoadImm):
    pass


class InstStore16bit(InstFamilyStoreImm):
    pass


class InstLoadAddr(InstFamilyLoadImm):
    pass


class InstStoreAddr(InstFamilyStoreImm):
    pass


class InstHighLoad(InstFamilyLoadImm):
    pass


class InstHighStore(InstFamilyStoreImm):
    pass


class InstHighCStore(InstFamilyStoreReg):
    pass


class InstHighCLoad(InstFamilyLoadReg):
    pass


class InstReset(InstFamilyRegWithImmediate):
    pass


class InstControl(InstFamilyOpOnly):
    pass


class InstCall(InstFamilyAddr):
    pass


class InstRet(InstFamilyOpOnly):
    pass


class InstConitionalRet(InstFamilyCondition):
    def __str__(self):
        return f"{self.op} {self.cond}"


class InstConitionalCall(InstFamilyCondition):
    pass


def main(gb_file):
    with open(gb_file, "rb") as f:
        code = f.read(0xa0)

    while len(code) > 0:
        inst, code = consume(code)
        print(inst)

    return 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("provide gb file")
        sys.exit(-1)

    sys.exit(main(sys.argv[1]))
