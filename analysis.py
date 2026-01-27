from pyboy import PyBoy
from lr35902dis import lr35902 as disassembler

# ===== BC / DE addressing =====
ST_BC_A        = 0x02  # LD (BC), A
LD_A_BC        = 0x0A  # LD A, (BC)

ST_DE_A        = 0x12  # LD (DE), A
LD_A_DE        = 0x1A  # LD A, (DE)


# ===== HL auto-increment =====
ST_HL_INC_A    = 0x22  # LD (HL+), A
LD_A_HL_INC    = 0x2A  # LD A, (HL+)


# ===== HL auto-decrement =====
ST_HL_DEC_A    = 0x32  # LD (HL-), A
LD_A_HL_DEC    = 0x3A  # LD A, (HL-)


# ===== (HL) <-> register =====
LD_B_HL        = 0x46  # LD B, (HL)
LD_C_HL        = 0x4E  # LD C, (HL)
LD_D_HL        = 0x56  # LD D, (HL)
LD_E_HL        = 0x5E  # LD E, (HL)
LD_H_HL        = 0x66  # LD H, (HL)
LD_L_HL        = 0x6E  # LD L, (HL)
LD_A_HL        = 0x7E  # LD A, (HL)

ST_HL_B        = 0x70  # LD (HL), B
ST_HL_C        = 0x71  # LD (HL), C
ST_HL_D        = 0x72  # LD (HL), D
ST_HL_E        = 0x73  # LD (HL), E
ST_HL_H        = 0x74  # LD (HL), H
ST_HL_L        = 0x75  # LD (HL), L
ST_HL_A        = 0x77  # LD (HL), A


# ===== High RAM / I/O =====
ST_IO_A8_A     = 0xE0  # LDH (a8), A
LD_A_IO_A8     = 0xF0  # LDH A, (a8)

ST_IO_C_A      = 0xE2  # LD (C), A
LD_A_IO_C      = 0xF2  # LD A, (C)


# ===== Absolute addressing =====
ST_A16_A       = 0xEA  # LD (a16), A
LD_A_A16       = 0xFA  # LD A, (a16)

LD_OPCODES = {
    # BC / DE
    LD_A_BC, LD_A_DE,

    # HL auto-inc / dec
    LD_A_HL_INC, LD_A_HL_DEC,

    # (HL) → register
    LD_B_HL, LD_C_HL, LD_D_HL, LD_E_HL, LD_H_HL, LD_L_HL, LD_A_HL,

    # High RAM / I/O
    LD_A_IO_A8, LD_A_IO_C,

    # Absolute
    LD_A_A16,
}

ST_OPCODES = {
    # BC / DE
    ST_BC_A, ST_DE_A,

    # HL auto-inc / dec
    ST_HL_INC_A, ST_HL_DEC_A,

    # register → (HL)
    ST_HL_B, ST_HL_C, ST_HL_D, ST_HL_E, ST_HL_H, ST_HL_L, ST_HL_A,

    # High RAM / I/O
    ST_IO_A8_A, ST_IO_C_A,

    # Absolute
    ST_A16_A,
}

GB_FILE = "mrdriller.gbc"
SYM_FILE = "mrdriller.sym"

symbols = {}

vars = 0
def gen_var():
    global vars
    s = f"Var_{vars}"
    vars += 1
    return s

def get_current_instruction(game):
    pc = game.register_file.PC
    inst = []
    dis = ""
    while not dis:
        inst.append(game.memory[pc])
        dis = disassembler.disasm(bytes(inst), 0)
        pc += 1
    return inst, dis

def main():
    game = PyBoy(GB_FILE)
    with open(SYM_FILE, "w") as f:
        while game.tick():
            inst, disasm = get_current_instruction(game)
            print(f"{game.register_file.PC:04X}:\t" +
                f"{" ".join(f"{i:02X}" for i in inst)}\t\t{disasm}")

            if inst[0] in LD_OPCODES:
                op = disassembler.decode(bytes(inst), 0)
                if inst[0] == LD_A_IO_A8:
                    key = op.operands[1][1] + 0xff00
                elif inst[0] == LD_A_IO_C:
                    key = game.register_file.C + 0xff00
                elif inst[0] == LD_A_DE:
                    d = game.register_file.D
                    e = game.register_file.E
                    key = (d << 8) & e
                elif inst[0] == LD_A_BC:
                    b = game.register_file.B
                    c = game.register_file.C
                    key = (b << 8) & c
                elif inst[0] == LD_A_A16:
                    key = op.operands[1][1]
                elif inst[0] in { LD_A_HL_INC, LD_A_HL_DEC, LD_B_HL,
                                  LD_C_HL, LD_D_HL, LD_E_HL, LD_H_HL,
                                  LD_L_HL, LD_A_HL }:
                    key = game.register_file.HL
                else:
                    import pdb; pdb.set_trace()
                    pass

                if key not in symbols:
                    symbols[key] = gen_var()
                    f.write(f"{key:04X} {symbols[key]}\n")

        game.stop()

if __name__ == "__main__":
    main()

vars = 0
arrs = 0

seen_addrs = []

#with open(symfile, "w") as f:
#    while game.tick():
#        pc = game.register_file.pc
#        inst = []
#        dis = ""
#        while not dis:
#            inst.append(game.memory[pc])
#            dis = disasm.disasm(bytes(inst), 0)
#            pc += 1
#        opcode_str = " ".join(f"{i:02X}" for i in inst)
#
#        if inst[0] in LOAD_INSTRUCTIONS:
#            op = disasm.decode(bytes(inst), 0)
#            print(f"{pc:04X}:\t{opcode_str}\t\t{dis}")
#            try:
#                ld_addr = op.operands[1][1]
#                if type(ld_addr) is int:
#                    if ld_addr not in seen_addrs:
#                        symbol = f"{ld_addr:04X}: VAR_{vars}"
#                        vars += 1
#                        seen_addrs.append(ld_addr)
#                        print(symbol)
#                        f.write(symbol + "\n")
#                elif ld_addr._name_.lower() == "hl":
#                    if game.register_file.HL not in seen_addrs:
#                        symbol = f"{game.register_file.HL:04X}: ARR_{arrs}"
#                        arrs += 1
#                        seen_addrs.append(game.register_file.HL)
#                        print(symbol)
#                        f.write(symbol + "\n")
#            except:
#                import pdb; pdb.set_trace()
#
#    game.stop()
