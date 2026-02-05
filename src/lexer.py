from abc import ABC, abstractmethod
import sys

instructions = []

class Instruction(ABC):
    @classmethod
    def register(cls):
        lst.append(cls)

    @abstractmethod
    def match(opcode: int) -> bool:
        pass

    register()

class InstALU(Instruction):
    @staticmethod
    def match(opcode):
        return (opcode >= 0x80 and opcode <= 0xC0) and not (opcode & 7 == 6)

    def __init__(self, op, regl, regr):
        self.op = op
        self.regl = regl
        self.regr = regr

class InstALU16bit(Instruction):
    pass

class InstALUDirect(Instruction):
    pass

class InstALUImmediate(Instruction):
    pass

class InstInc8bit(Instruction):
    pass

class InstInc16bit(Instruction):
    pass

class InstDec8bit(Instruction):
    pass

class InstDec16bit(Instruction):
    pass


class InstCBPrefix(Instruction):
    pass

class InstRelJumpConditional(Instruction):
    pass

class InstAbsJumpConditional(Instruction):
    pass


class InstPush(Instruction):
    pass

class InstPop(Instruction):
    pass


class InstLoadRegToReg(Instruction):
    pass


class InstLoadRegToHL(Instruction):
    pass


class InstLoadHLToReg(Instruction):
    pass

class InstLoadRegToHLI(Instruction):
    pass

class InstLoadHLIToReg(Instruction):
    pass


class InstLoadAddr(Instruction):
    pass

class InstStoreAddr(Instruction):
    pass

class InstHighLoad(Instruction):
    pass

class InstHighStore(Instruction):
    pass

class InstHighCStore(Instruction):
    pass

class InstHighCLoad(Instruction):
    pass

class InstControl(Instruction):
    pass

class InstCall(Instruction):
    pass

class instRet(Instruction):
    pass


def main(gb_file):
    with open(gb_file, "rb") as f:
        code = f.read(0xa0)
    print(code)

    return 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("provide gb file")
        sys.exit(-1)

    sys.exit(main(sys.argv[1]))
