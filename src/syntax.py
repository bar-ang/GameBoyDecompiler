from abc import ABC, abstractmethod

class Instruction(ABC):

    def __init__(self, op:str, regl:str=None, regr:str=None, *, imm:int=0, addr:int=0, cond:str=""):
        self.op = op
        self.regl = regl
        self.regr = regr
        self.imm = imm
        self.addr = addr
        self.cond = cond

    def __str__(self):
        return f"{self.op} {self.cond} {self.regl}, {self.regr}, {self.imm:02x}, ({self.addr:04x})"


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


