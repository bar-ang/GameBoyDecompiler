from syntax import *
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
        return InstALU("SCF"), code[1:]

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

        return InstALU(op, regr=reg), code[n_bytes:]

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

        return InstALU16bit("ADD", "HL", reg_order[reg]), code[n_bytes:]

    elif opcode == 0xE8:
        # ADD SP, r8
        n_bytes = 2

        return InstALUregSP("ADD", "SP", code[1]), code[n_bytes:]

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


def main(gb_file):
    with open(gb_file, "rb") as f:
        code = f.read(0x100)

    while len(code) > 0:
        inst, code = consume(code)
        print(inst)

    return 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("provide gb file")
        sys.exit(-1)

    sys.exit(main(sys.argv[1]))
