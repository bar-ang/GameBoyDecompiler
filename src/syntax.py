from abc import ABC, abstractmethod
from expr import Expr
from enum import Enum

class Operator(Enum):
    LD = "LD"
    JP = "JP"
    JR = "JR"
    CALL = "CALL"
    RET = "RET"
    RETI = "RETI"
    RST = "RST"
    RLCA = "RLCA"
    RLA  = "RLA"
    RRCA = "RRCA"
    RRA  = "RRA"
    DAA = "DAA"
    SCF = "SCF"
    CCF = "CCF"
    INC = "INC"
    DEC = "DEC"
    POP = "POP"
    PUSH = "PUSH"
    ADD = "ADD"
    ADC = "ADC"
    SUB = "SUB"
    SBC = "SBC"
    AND = "AND"
    OR = "OR"
    XOR = "XOR"
    CPL = "CPL"
    CP = "CP"
    NOP = "NOP"
    STOP = "STOP 0"
    HALT = "HALT"
    CB = "CB"
    DI = "DI"
    EI = "EI"
    BETA = "β"

    def __str__(self):
        return f"{self.value}"

class Reg(Enum):
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

    def __str__(self):
        return f"{self.value}"

class Direct(Enum):
    BC = (Reg.B, Reg.C, 0)
    DE = (Reg.D, Reg.E, 0)
    AF = (Reg.A, Reg.F, 0)
    HL = (Reg.H, Reg.L, 0)
    HLPlus = (Reg.H, Reg.L, 1)
    HLMinus = (Reg.H, Reg.L, -1)

    def __str__(self):
        suff = ""
        if self.value[2] > 0:
            suff = "+"
        elif self.value[2] < 0:
            suff = "-"
        return f"{self.value[0]}{self.value[1]}{suff}"

class Cond(Enum):
    C = "C"
    Z = "Z"
    NC = "NC"
    NZ = "NZ"

    def __str__(self):
        return f"{self.value}"

class Deref:
    def __init__(self, operand : Reg | Direct | int):
        self._operand = operand

    @property
    def operand(self):
        return self._operand

    def __str__(self):
        return f"[{self.operand}]"

OpdType = Reg | Deref | Direct | Cond | int


def create_initial_regmap():
    return {
        Reg.A : 0x11,
        Reg.B : 0,
        Reg.C : 0,
        Reg.D : 0xff,
        Reg.E : 0x56,
        Reg.F : 0x80,
        Reg.H : 0,
        Reg.L : 0xd,
        Reg.SP : 0xfffe,
        Reg.PC : 0x100,
        Reg.Stack: []
    }

class Instruction(ABC):

    def __init__(self,
                 op: Operator | None=None,
                 left: OpdType | None=None,
                 right: OpdType | None=None):
        self._op = op
        self.left = left
        self.right = right

    @property
    def operand(self):
        assert (self.left or self.right) and not (self.left and self.right)
        return self.left or self.right

    @property
    def op(self):
        return self._op

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        res = f"{self.op}"
        if self.left:
            left_str = str(self.left)
            if left_str.isdigit():
                left_str = f"${int(left_str):04X}"
            res += f" {left_str}"
        if self.right:
            right_str = str(self.right)
            if right_str.isdigit():
                right_str = f"${int(right_str):04X}"
            res += f", {right_str}"

        return res

    def dry_run(self, regmap):
        pass


class InstControl(Instruction):
    def __init__(self, op: Operator):
        super().__init__(op)


class InstFlow(Instruction):
    def __init__(self, op: Operator, cond: Cond | None=None, addr: int | None=None):
        super().__init__(op, cond, addr)

    @property
    def cond(self):
        return self.left

    @property
    def addr(self):
        return self.right


class InstJump(InstFlow):
    def __init__(self, op: Operator, addr: int, cond: Cond | None=None):
        assert op in {Operator.JR, Operator.JP}
        super().__init__(op, cond=cond, addr=addr)

    def is_relative(self) -> bool:
        return self.op == Operator.JR


class InstConditionalJr(InstJump):
    def __init__(self, cond: Cond, addr: int):
        assert addr < 256
        if addr >= 128:
            addr -= 256
        super().__init__(Operator.JR, cond=cond, addr=addr)


class InstConditionalJp(InstJump):
    def __init__(self, cond: Cond, addr: int):
        super().__init__(Operator.JP, cond=cond, addr=addr)


class InstJr(InstJump):
    def __init__(self, addr: int):
        assert addr < 256
        if addr >= 128:
            addr -= 256
        super().__init__(Operator.JR, addr=addr)


class InstJp(InstJump):
    def __init__(self, addr: int):
        super().__init__(Operator.JP, addr=addr)


class InstCall(InstFlow):
    def __init__(self, addr: int):
        super().__init__(Operator.CALL, addr=addr)


class InstRet(InstFlow):
    def __init__(self):
        super().__init__(Operator.RET)

class InstReti(InstFlow):
    def __init__(self):
        super().__init__(Operator.RET)


class InstConditionalRet(InstFlow):
    def __init__(self, cond: Cond):
        super().__init__(Operator.RET, cond)


class InstConditionalCall(InstFlow):
    def __init__(self, cond: Cond, addr: int):
        super().__init__(Operator.CALL, addr=addr)


class InstLd8bit(Instruction):
    def __init__(self, left: OpdType, right: OpdType):
        super().__init__(Operator.LD, left, right)


class InstLdhLoad(InstLd8bit):
    def __init__(self, addr: int):
        super().__init__(Reg.A, addr + 0xff00)


class InstLdhStore(InstLd8bit):
    def __init__(self, addr: int):
        super().__init__(addr + 0xff00, Reg.A)


class InstLdhCLoad(InstLd8bit):
    def __init__(self):
        super().__init__(Reg.A, Deref(Reg.C))


class InstLdhCStore(InstLd8bit):
    def __init__(self):
        super().__init__(Deref(Reg.C), Reg.A)

class InstLd16bit(InstLd8bit):
    def __init__(self, left: Direct, right: Direct):
        super().__init__(left, right)


class InstPop(Instruction):
    def __init__(self, direct: Direct):
        super().__init__(Operator.POP, left=direct)


class InstPush(Instruction):
    def __init__(self, direct: Direct):
        super().__init__(Operator.PUSH, left=direct)


class InstALU8bit(Instruction):
    def __init__(self, op: Operator, operand: OpdType=Reg.A):
        super().__init__(op, left=Reg.A, right=operand)


class InstALU16bit(Instruction):
    def __init__(self, op: Operator, operand: Direct):
        super().__init__(op, left=Direct.HL, right=operand)


class InstRotShift(Instruction):
    def __init__(self, op: Operator, operand: OpdType=Reg.A):
        super().__init__(op, left=operand)


class InstRst(Instruction):
    def __init__(self, imm:int):
        super().__init__(Operator.RST, left=imm)


class InstInc(Instruction):
    def __init__(self, reg: OpdType):
        super().__init__(Operator.INC, reg)


class InstDec(Instruction):
    def __init__(self, reg: OpdType):
        super().__init__(Operator.DEC, reg)


class InstAddRegSP(InstALU8bit):
    def __init__(self, r8: int):
        super().__init__(Operator.ADD, operand=r8)
