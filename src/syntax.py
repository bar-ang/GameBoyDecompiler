from abc import ABC, abstractmethod
from expr import Expr
from enum import Enum

class Regs(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    H = "H"
    L = "L"

    SP = "SP"
    PC = "PC"
    Stack = "Stack"

def create_initial_regmap():
    return {
#        Regs.A : 0x11,
#        Regs.B : 0,
#        Regs.C : 0,
#        Regs.D : 0xff,
#        Regs.E : 0x56,
#        Regs.F : 0x80,
#        Regs.H : 0,
#        Regs.L : 0xd,
#        Regs.SP : 0xfffe,
#        Regs.PC : 0x100,
        "A" : 0x11,
        "B" : 0,
        "C" : 0,
        "D" : 0xff,
        "E" : 0x56,
        "F" : 0x80,
        "H" : 0,
        "L" : 0xd,
        "PC" : 0x100,
        "Stack": []
    }

class Instruction(ABC):

    def __init__(self, op:str, regl:str=None, regr:str=None, *, imm:int=0, addr:int=0, cond:str=""):
        self._op = op
        self.regl = regl
        self.regr = regr
        self.imm = imm
        self.addr = addr
        self.cond = cond

    @property
    def op(self):
        return self._op

    def __str__(self):
        return f"{self.op} {self.cond} {self.regl}, {self.regr}, {self.imm:02x}, ({self.addr:04x})"

    @abstractmethod
    def dry_run(self, regmap):
        pass


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
    def __init__(self, op, reg="A", imm=0):
        return super().__init__(op, reg, imm=imm)

    def __str__(self):
        return f"{self.op} {self.regl}, ${self.imm:04x}"


class InstFamilyAddr(Instruction):
    def __init__(self, op, addr):
        return super().__init__(op, addr=addr)

    def __str__(self):
        return f"{self.op} ${self.addr:04x}"


class InstFamilyDirect(Instruction):
    def __init__(self, op, reg="HL"):
        return super().__init__(op, reg)

    def __str__(self):
        return f"{self.op} ({self.regl})"


class InstFamilyStoreReg(Instruction):
    def __init__(self, op, regl="HL", regr="A"):
        return super().__init__(op, regl, regr)

    def __str__(self):
        return f"{self.op} ({self.regl}), {self.reg}"


class InstFamilyLoadReg(Instruction):
    def __init__(self, op, regl="A", regr="HL"):
        return super().__init__(op, regl, regr)

    def __str__(self):
        return f"{self.op} {self.regl}, ({self.regr})"


class InstFamilyStoreAddr(Instruction):
    def __init__(self, op, addr, reg):
        return super().__init__(op, regr=reg, addr=addr)

    def __str__(self):
        return f"{self.op} (${self.addr:04x}), {self.regr}"


class InstFamilyLoadAddr(Instruction):
    def __init__(self, op, reg, addr):
        return super().__init__(op, regl=reg, addr=addr)

    def __str__(self):
        return f"{self.op} {self.regr}, (${self.addr:04x})"


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



class InstALUregSP(InstFamilyRegWithImmediate):
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
    def dry_run(self, regmap):
        assert self.regl in regmap
        val = regmap[self.regl]
        sign = "+" if self.op.upper() == "INC" else "-"
        val = Expr(sign, val, "1")
        regmap[self.regl] = val
        return None


class InstIncDecDirect(InstFamilyDirect):
    pass


class InstIncDec16bit(InstFamilySingleReg):
    pass


class InstCBPrefixDirect(InstFamilyDirect):
    pass


class InstCBPrefix(InstFamilySingleReg):
    pass


class InstRelJumpConditional(InstFamilyCondition):
    def __init__(self, op, cond, addr):
        if addr >= 128:
            addr = addr - 256
        return super().__init__(op, cond=cond, addr=addr)


class InstAbsJumpConditional(InstFamilyCondition):
    pass


class InstRelJump(InstFamilyAddr):
    def __init__(self, op, addr):
        if addr >= 128:
            addr = addr - 256
        return super().__init__(op, addr=addr)

    def dry_run(self, regmap):
        return None


class InstAbsJump(InstFamilyAddr):
    def dry_run(self, regmap):
        return None


class InstPush(InstFamilyTwoRegs):
    def __init__(self, op, highreg, lowreg):
        super().__init__(op, regl=highreg, regr=lowreg)

    def dry_run(self, regmap):
        regmap["Stack"].append((self.regl, self.regr))

class InstPop(InstFamilyTwoRegs):
    def __init__(self, op, highreg, lowreg):
        super().__init__(op, regl=highreg, regr=lowreg)

    def dry_run(self, regmap):
        l, r = regmap["Stack"][-1]
        regmap["Stack"] = regmap["Stack"][:-1]
        regmap[self.regl] = regmap[l]
        regmap[self.regr] = regmap[r]


class InstLoadImmediate16bit(InstFamilyRegWithImmediate):
    def dry_run(self, regmap):
        assert self.reg in regmap
        regmap[self.reg] = self.imm

        return None

class InstLoadImmediate(InstFamilyRegWithImmediate):
    def dry_run(self, regmap):
        assert self.regl in regmap, self.regl
        regmap[self.regl] = f"${self.imm:02x}"
        return None

class InstLoadDirect(InstFamilyLoadReg):
    pass


class InstLoadRegToReg(InstFamilyTwoRegs):
    def dry_run(self, regmap):
        regmap[self.regl] = regmap[self.regr]
        return None

class InstLoadRegToHL(InstFamilyStoreReg):
    pass


class InstLoadHLToReg(InstFamilyLoadReg):
    pass


class InstLoadRegToHLI(InstFamilyStoreReg):
    pass


class InstLoadHLIToReg(InstFamilyLoadReg):
    pass


class InstLoadImmediateDirect(Instruction):
    def __init__(self, op, imm, reg="HL"):
        return super().__init__(op, regl=reg, imm=imm)

    def __str__(self):
        return f"{self.op} ({self.regl}), {self.imm:02x}"
    

class InstLoad16bit(InstFamilyLoadReg):
    pass


class InstStore16bit(InstFamilyStoreReg):
    pass


class InstLoadAddr(InstFamilyLoadAddr):
    pass


class InstStoreAddr(InstFamilyStoreAddr):
    def dry_run(self, regmap):
        assert self.regr in regmap
        val = Expr(":=", f"${self.addr:04x}", regmap[self.regr])
        return val


class InstHighLoad(InstFamilyLoadAddr):
    pass


class InstHighStore(InstFamilyStoreAddr):
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


