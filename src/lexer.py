from syntax import *
import sys

DIRECT_OP = Deref(Direct.HL)

REG_ORDER:   list[Reg | Deref]        = [Reg.B, Reg.C, Reg.D, Reg.E, Reg.H, Reg.L, DIRECT_OP, Reg.A]
REG16_ORDER: list[Direct]   = [Direct.BC, Direct.DE, Direct.HLPlus, Direct.HLMinus]
OP_ORDER:    list[Operator]    = [Operator.ADD, Operator.ADC, Operator.SUB, Operator.SBC, Operator.AND, Operator.XOR, Operator.OR, Operator.CP]
COND_ORDER:  list[Cond]      = [Cond.NZ, Cond.Z, Cond.NC, Cond.C]
INC_ORDER:   list[Operator]   = [Operator.INC, Operator.DEC]

def inc_or_dec(op, reg: Reg):
    if op == Operator.INC:
        return InstInc(reg)
    return InstDec(reg)


class UnknownInstructionException(Exception):
    pass



def attach_two_bytes(bts, endianness=0):
    return bts[endianness] | (bts[1 - endianness] << 8)

def consume(code, pos, endianness="little") -> tuple[Instruction, int]:
    assert endianness in ("big", "little")
    endianness = 0 if endianness == "little" else 1

    opcode = code[pos]

    if opcode == 0x76:
        return InstControl(Operator.HALT), 1

    elif opcode == 0x07:
        return InstRotShift(Operator.RLCA), 1

    elif opcode == 0x17:
        return InstRotShift(Operator.RLA), 1

    elif opcode == 0x0F:
        return InstRotShift(Operator.RRCA), 1

    elif opcode == 0x1F:
        return InstRotShift(Operator.RRA), 1

    elif opcode == 0x00:
        return InstControl(Operator.NOP), 1

    elif opcode == 0x10:
        return InstControl(Operator.STOP), 2

    elif opcode == 0x27:
        return InstALU8bit(Operator.DAA), 1

    elif opcode == 0x37:
        return InstALU8bit(Operator.SCF), 1

    elif opcode == 0x2F:
        return InstALU8bit(Operator.CPL), 1

    elif opcode == 0x3F:
        return InstALU8bit(Operator.CCF), 1

    elif opcode == 0xF3:
        return InstControl(Operator.DI), 1

    elif opcode == 0xFB:
        return InstControl(Operator.EI), 1

    elif opcode >= 0x80 and opcode < 0xC0:
        # most 8-bit arithmatic commands have opcodes $80-$bf
        # with register ordered: B, C, D, E, H, L, (HL), A
        # all codes in this range do not take constant values
        # therefore they're 1-byte length each.
        n_bytes = 1
        op = OP_ORDER[(opcode & 0x38) >> 3]
        if opcode & 7 == 6: # has memory access: op a, (HL)
            return InstALU8bit(op, Deref(Direct.HL)), n_bytes
        reg = REG_ORDER[opcode & 7]

        return InstALU8bit(op, operand=reg), n_bytes

    elif opcode & 0xF0 in {0x20, 0x30} and opcode & 7 == 0:
        # these are the conditional JR commands
        n_bytes = 2
        offset = code[pos+1]
        cond = COND_ORDER[(opcode & 0x18) >> 3]

        return InstConditionalJr(cond=cond, addr=offset), n_bytes

    elif opcode & 0xF0 in {0xC0, 0xD0} and opcode & 7 == 2:
        # these are the conditional JP commands
        n_bytes = 3
        pc = attach_two_bytes(code[pos+1:pos+3], endianness)
        cond = COND_ORDER[(opcode & 0x18) >> 3]

        return InstConditionalJp(cond=cond, addr=pc), n_bytes

    elif opcode == 0xC3:
        # unconditional JP command
        n_bytes = 3
        pc = attach_two_bytes(code[pos+1:pos+3], endianness)

        return InstJp(addr=pc), n_bytes

    elif opcode == 0x18:
        # unconditional JR command
        return InstJr(addr=code[pos+1]), 2

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
        return InstLd8bit(REG_ORDER[dst], REG_ORDER[src]), n_bytes

    elif opcode >= 0xC0 and opcode & 7 == 7:
        # RST commands
        val = opcode & 0x38
        return InstRst(imm=val), 1

    elif opcode == 0xEA: # LD (a16),A
        n_bytes = 3
        n = attach_two_bytes(code[pos+1:pos+3], endianness)

        return InstLd8bit(Deref(n), Reg.A), n_bytes

    elif opcode == 0xFA: # LD A,(a16)
        n_bytes = 3
        n = attach_two_bytes(code[pos+1:pos+3], endianness)

        return InstLd8bit(Reg.A, Deref(n)), n_bytes

    elif opcode >= 0xC0 and opcode & 7 == 6:
        # these are all 2-byte commands operating on reg A
        n_bytes = 2
        op = (opcode & 0x38) >> 3

        return InstALU8bit(OP_ORDER[op], operand=code[pos+1]), n_bytes

    elif opcode < 0x40 and opcode & 7 in {4, 5}:
        # these are all 1-byte commands with the standard reg order
        # INC and DEC.
        n_bytes = 1

        reg = ((opcode & 8) | (opcode & 0x30)) >> 3
        op = opcode & 3
        return inc_or_dec(INC_ORDER[op], REG_ORDER[reg]), n_bytes

    elif opcode < 0x40 and opcode & 7 == 6:
        # 2-bytes LD commands
        n_bytes = 2

        reg = ((opcode & 8) | (opcode & 0x30)) >> 3
        return InstLd8bit(left=REG_ORDER[reg], right=code[pos+1]), n_bytes

    elif opcode < 0x40 and opcode & 7 == 2:
        # these are LD commands or the form:
        #    LD A, (reg16)
        # or LD (reg16), A
        n_bytes = 1

        reg = (opcode & 0x30) >> 4
        if opcode & 0xf == 2: # store
            return InstLd8bit(Deref(REG16_ORDER[reg]), Reg.A), n_bytes
        else: # load
            return InstLd8bit(Reg.A, Deref(REG16_ORDER[reg])), n_bytes

    elif opcode == 0xCB:
        #TODO for now, we won't identify the command exactly
        n_bytes = 2

        op = code[pos+1]
        reg = op & 7
        beta =  op >> 3

        return InstRotShift(Operator.BETA, REG_ORDER[reg]), n_bytes

    elif opcode < 0x40 and opcode & 0xF == 1:
        # 16 bits immediate value LD commands
        n_bytes = 3
        reg_order = [Direct.BC, Direct.DE, Direct.HL, Reg.SP]
        reg = opcode >> 4
        n = attach_two_bytes(code[pos+1:pos+3], endianness)

        return InstLd16bit(reg_order[reg], right=n), n_bytes

    elif opcode < 0x40 and opcode & 0x7 == 3:
        # 16 bits INC and DEC
        n_bytes = 1
        reg_order = [Direct.BC, Direct.DE, Direct.HL, Reg.SP]
        reg = opcode >> 4
        op = opcode & 1

        return inc_or_dec(INC_ORDER[op], reg_order[reg]), n_bytes

    elif opcode < 0x40 and opcode & 0xF == 9:
        # ADD HL, r16
        n_bytes = 1
        reg_order = [Direct.BC, Direct.DE, Direct.HL, Reg.SP]
        reg = opcode >> 4

        return InstALU16bit(Operator.ADD, reg_order[reg]), n_bytes

    elif opcode == 0xE8:
        # ADD SP, r8
        n_bytes = 2

        return InstAddRegSP(code[pos+1]), n_bytes

    elif opcode >= 0xC0 and opcode & 0xF == 1:
        # POP commands
        n_bytes = 1
        reg_order = [Direct.BC, Direct.DE, Direct.HL, Direct.AF]
        reg = (opcode & 0x30) >> 4

        return InstPop(reg_order[reg]), n_bytes

    elif opcode >= 0xC0 and opcode & 0xF == 5:
        # PUSH commands
        n_bytes = 1
        reg_order = [Direct.BC, Direct.DE, Direct.HL, Direct.AF]
        reg = (opcode & 0x30) >> 4

        return InstPush(reg_order[reg]), n_bytes

    elif opcode == 0xE0:
        # LDH (addr), A
        n_bytes = 2

        return InstLdhStore(code[pos+1]), n_bytes

    elif opcode == 0xF0:
        # LDH A, (addr)
        n_bytes = 2

        return InstLdhLoad(code[pos+1]), n_bytes

    elif opcode == 0xE2:
        # LD (C), A
        n_bytes = 2

        return InstLdhCStore(), n_bytes

    elif opcode == 0xF2:
        # LD A, (C)
        n_bytes = 2

        return InstLdhCLoad(), n_bytes

    elif opcode == 0xC9:
        return InstRet(), 1

    elif opcode == 0xD9:
        return InstReti(), 1

    elif opcode & 0xF0 in {0xC0, 0xD0} and opcode & 7 == 0:
        # Conditional RET
        n_bytes = 1
        cond = COND_ORDER[(opcode & 0x18) >> 3]

        return InstConditionalRet(cond=cond), n_bytes

    elif opcode == 0xCD:
        # unconditional CALL
        n_bytes = 3
        n = attach_two_bytes(code[pos+1:pos+3], endianness)

        return InstCall(addr=n), n_bytes

    elif opcode & 0xF0 in {0xC0, 0xD0} and opcode & 7 == 4:
        # Conditional CALL
        n_bytes = 3
        pc = attach_two_bytes(code[pos+1:pos+3], endianness)
        cond = COND_ORDER[(opcode & 0x18) >> 3]

        return InstConditionalCall(addr=pc, cond=cond), n_bytes


    raise UnknownInstructionException(f"Unknown instruction: {opcode:02X}")


def tokenize_code(code, start_pc=0):
    tokcode = []
    pc = start_pc
    codelen = len(code)
    while pc < start_pc + codelen:
        try:
            inst, n_bytes = consume(code, pc)
            tokcode.append((pc, inst))
            pc += n_bytes
        except UnknownInstructionException:
            pc += 1

    return tokcode

def main(gb_file):
    with open(gb_file, "rb") as f:
        code = f.read()

    toks = tokenize_code(code)
    print("\n".join([str(t[1]) for t in toks]))

    return 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("provide gb file")
        sys.exit(-1)

    sys.exit(main(sys.argv[1]))
