from opcodes import *
from pyboy import PyBoy
from lr35902dis import lr35902 as disassembler

GB_FILE = "mrdriller.gbc"
SYM_FILE = "mrdriller.sym"

symbols = {}
func_symbols = {}

vars = {}
def gen_var(prefix="Var"):
    if prefix not in vars:
        vars[prefix] = 0
    s = f"{prefix}_{vars[prefix]}"
    vars[prefix] += 1
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

    read_vars = []
    write_vars = []

    while game.tick():
        inst, disasm = get_current_instruction(game)

        print(f"{game.register_file.PC:04X}:\t" +
            f"{" ".join(f"{i:02X}" for i in inst)}\t\t{disasm}")
        op = disassembler.decode(bytes(inst), 0)

        if inst[0] in LD_OPCODES or inst[0] in ST_OPCODES:
            if inst[0] == LD_A_IO_A8:
                key = op.operands[1][1] + 0xff00
            elif inst[0] == ST_IO_A8_A:
                key = op.operands[0][1] + 0xff00
            elif inst[0] in {LD_A_IO_C, ST_IO_C_A}:
                key = game.register_file.C + 0xff00
            elif inst[0] in {LD_A_DE, ST_DE_A}:
                d = game.register_file.D
                e = game.register_file.E
                key = (d << 8) & e
            elif inst[0] in {LD_A_BC, ST_BC_A}:
                b = game.register_file.B
                c = game.register_file.C
                key = (b << 8) & c
            elif inst[0] == LD_A_A16:
                key = op.operands[1][1]
            elif inst[0] == ST_A16_A:
                key = op.operands[0][1]
            elif inst[0] in HL_OP_GROUP:
                key = game.register_file.HL
            else:
                raise Exception(f"Unknown opcode {inst[0]:02X}.")

            if key not in symbols:
                symbols[key] = gen_var("Temp")

            if inst[0] in LD_OPCODES:
                read_vars.append(key)
            else:
                write_vars.append(key)

        elif inst[0] in CALL_COMMANDS:
            if inst[0] == CALL_A16:
                key = op.operands[0][1]
            else:
                # all other CALL cmds are very rare
                import pdb; pdb.set_trace()
                pass

            if key not in func_symbols:
                func_symbols[key] = gen_var("Func")

    game.stop()
    with open(SYM_FILE, "w") as f:
        for k, _ in symbols.items():
            assert k in read_vars or k in write_vars
            if k in read_vars and k in write_vars:
                v = gen_var("Var")
            elif k in read_vars:
                v = gen_var("Const")
            else:
                v = gen_var("WOnly")
            f.write(f"{k:04X} {v}\n")

        for k, v in func_symbols.items():
            f.write(f"{k:04X} {v}\n")

if __name__ == "__main__":
    main()
