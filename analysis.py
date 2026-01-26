from pyboy import PyBoy
from lr35902dis import lr35902 as disasm

game = PyBoy('mrdriller.gbc')

while game.tick():
    pc = game.register_file.PC
    inst = [game.memory[pc]]
    dis = ""
    while not dis:
        inst.append(game.memory[pc])
        dis = disasm.disasm(bytes(inst), 0)
        pc += 1
    opcode_str = " ".join(f"{i:02X}" for i in inst)
    print(f"{pc:04X}:\t{opcode_str}\t\t{dis}")
game.stop()
