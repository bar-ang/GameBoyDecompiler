from abc import ABC, abstractmethod
from expr import Expr
from enum import Enum
from typing import cast

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
    RLC = "RLC"
    RRC = "RRC"
    RL = "RL"
    RR = "RR"
    SLA = "SLA"
    SRA = "SRA"
    SWAP = "SWAP"
    SRL = "SRL"
    BIT = "BIT"
    RES = "RES"
    SET = "SET"

    def __str__(self):
        return f"{self.value}"

SIGNS = {
    Operator.ADD: "+",
    Operator.SUB: "-",
    Operator.ADC: "+`",
    Operator.SBC: "-`",
    Operator.INC: "+",
    Operator.DEC: "-",
    Operator.CP: "-",
    Operator.CPL: "~",
    Operator.OR:  "|",
    Operator.XOR: "^",
    Operator.AND: "&",
    Operator.SLA: "<<1",
    Operator.SRA: ">>`1",
    Operator.SWAP: "SWAP", # TODO: no existing sign for that
    Operator.SRL: "<<1",
    Operator.BIT: ":",     # TODO: no existing sign for that
    Operator.SET: "-on",   # TODO: no existing sign for that
    Operator.RES: "-off",  # TODO: no existing sign for that 
    Operator.RR: "RR"
}

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

# NOTE: we take the opposite of the ASM command!
CONDITIONS = {
    Cond.C: ">=",
    Cond.Z: "!=",
    Cond.NC: "<",
    Cond.NZ: "==",
}

class Deref:
    def __init__(self, operand : Reg | Direct | int):
        self._operand = operand

    @property
    def operand(self) ->  Reg | Direct | int:
        return self._operand

    def __str__(self) -> str:
        return f"[{self.operand}]"

OpdType = Reg | Deref | Direct | Cond | int

TypeRegmap = dict[Reg, Expr]
TypeStack = list[Expr]

def create_initial_regmap() -> tuple[TypeRegmap, TypeStack]:
    return {
        Reg.A : Expr(0x11),
        Reg.B : Expr(0),
        Reg.C : Expr(0),
        Reg.D : Expr(0xff),
        Reg.E : Expr(0x56),
        Reg.F : Expr(0x80),
        Reg.H : Expr(0),
        Reg.L : Expr(0xd),
        Reg.SP : Expr(0xfffe),
        Reg.PC : Expr(0x100),
    }, []

def r_value(val: OpdType | None, regmap : TypeRegmap) -> Expr:
    assert val is not None
    assert not isinstance(val, Cond)

    if isinstance(val, int):
        return Expr(val)
    elif isinstance(val, Reg):
        return regmap[val]
    elif isinstance(val, Deref):
        return Expr("*", r_value(val.operand, regmap))
    elif isinstance(val, Direct):
        h, l, i = val.value
        assert i == 0
        return Expr(".", regmap[h], regmap[l])
    raise Exception(f"could not handle r-value '{val}' of type '{type(val)}'")

class Instruction(ABC):

    @staticmethod
    def Empty() -> 'Instruction':
        return InstControl(Operator.NOP)

    def __init__(self,
                 op: Operator | None=None,
                 left: OpdType | None=None,
                 right: OpdType | None=None):
        self._op = op
        self.left = left
        self.right = right

    @property
    def operand(self) -> OpdType:
        assert (self.left or self.right) and not (self.left and self.right)
        return cast(OpdType, self.left or self.right)

    @property
    def op(self) -> Operator:
        assert self._op
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

    @abstractmethod
    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
        pass


class InstControl(Instruction):
    def __init__(self, op: Operator):
        super().__init__(op)

    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
        return None

class InstFlow(Instruction):
    def __init__(self, op: Operator, cond: Cond | None=None, addr: int | None=None):
        super().__init__(op, cond, addr)

    @property
    def cond(self):
        return self.left

    @property
    def addr(self):
        return self.right

    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
        return None


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

    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
       return None

class InstReti(InstFlow):
    def __init__(self):
        super().__init__(Operator.RET)

    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
       return None


class InstConditionalRet(InstFlow):
    def __init__(self, cond: Cond):
        super().__init__(Operator.RET, cond)


class InstConditionalCall(InstFlow):
    def __init__(self, cond: Cond, addr: int):
        super().__init__(Operator.CALL, addr=addr)


class InstLd8bit(Instruction):
    def __init__(self, left: OpdType, right: OpdType):
        super().__init__(Operator.LD, left, right)

    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
        assert not isinstance(self.left, Cond)
        assert not isinstance(self.left, int)
        rv = r_value(self.right, regmap)
        if isinstance(self.left, Reg):
            regmap[self.left] = rv
            return None
        elif isinstance(self.left, Direct):
            h, l, i = self.left.value
            assert i == 0, "unimplemented"
            regmap[h] = rv.high
            regmap[l] = rv.low
            return None
        elif isinstance(self.left, Deref):
            inner = self.left.operand
            return Expr(":=", Expr("*", r_value(inner, regmap)), rv)

        raise Exception(f"cannot handle LD left value that is '{self.left}' of type '{type(self.left)}'")
        return None


class InstLdhLoad(InstLd8bit):
    def __init__(self, addr: int):
        super().__init__(Reg.A, Deref(addr + 0xff00))


class InstLdhStore(InstLd8bit):
    def __init__(self, addr: int):
        super().__init__(Deref(addr + 0xff00), Reg.A)


class InstLdhCLoad(InstLd8bit):
    def __init__(self):
        super().__init__(Reg.A, Deref(Reg.C))


class InstLdhCStore(InstLd8bit):
    def __init__(self):
        super().__init__(Deref(Reg.C), Reg.A)

class InstLd16bit(InstLd8bit):
    def __init__(self, left: Direct, right: Direct):
        super().__init__(left, right)


class InstStack(Instruction):
    def __init__(self, op: Operator, direct: Direct):
        super().__init__(op, left=direct)

    @abstractmethod
    def update_stack(self, regmap: TypeRegmap, stack: TypeStack):
        pass


class InstPop(InstStack):
    def __init__(self, direct: Direct):
        super().__init__(Operator.POP, direct=direct)

    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
       regmap[Reg.SP] = Expr("-", regmap[Reg.SP], Expr(2))
       return None

    def update_stack(self, regmap: TypeRegmap, stack: TypeStack):
       assert isinstance(self.left, Direct)
       h, l, i = self.left.value
       assert i == 0
       regmap[h] = stack.pop()
       regmap[l] = stack.pop()


class InstPush(InstStack):
    def __init__(self, direct: Direct):
        super().__init__(Operator.PUSH, direct=direct)

    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
       regmap[Reg.SP] = Expr("+", regmap[Reg.SP], Expr(2))
       return None

    def update_stack(self, regmap : TypeRegmap, stack: TypeStack):
       assert isinstance(self.left, Direct)
       h, l, i = self.left.value
       assert i == 0
       stack.append(regmap[l])
       stack.append(regmap[h])

class InstALU8bit(Instruction):
    def __init__(self, op: Operator, operand: OpdType=Reg.A):
        super().__init__(op, left=Reg.A, right=operand)

    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
        assert self.left
        assert not isinstance(self.left, Cond)
        assert not isinstance(self.left, Direct)
        assert not isinstance(self.left, Deref)
        assert not isinstance(self.left, int)
        rv = r_value(self.right, regmap)
        regmap[self.left] = Expr(SIGNS.get(self.op, self.op.value), regmap[self.left], rv)
        return None


class InstALU16bit(Instruction):
    def __init__(self, op: Operator, operand: Direct):
        super().__init__(op, left=Direct.HL, right=operand)

    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
        return None


class InstRotShift(Instruction):
    def __init__(self, op: Operator, operand: OpdType=Reg.A):
        super().__init__(op, left=operand, right=operand)

    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
        assert isinstance(self.left, Reg)

        regmap[self.left] = Expr(SIGNS[self.op], regmap[self.left])
        return None


class InstBit(Instruction):
    def __init__(self, op: Operator, bit: int, operand: OpdType=Reg.A):
        super().__init__(op, left=bit, right=operand)

    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
        assert isinstance(self.left, int)
        assert isinstance(self.right, Reg)
        assert self.left >= 0 and self.left < 10

        regmap[self.right] = Expr(SIGNS[self.op], regmap[self.right], Expr(self.left))
        return None

class InstRst(Instruction):
    def __init__(self, imm:int):
        super().__init__(Operator.RST, left=imm)

    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
        return None

class InstIncDec(Instruction):
    def __init__(self, op: Operator, reg: OpdType):
        assert op == Operator.INC or op == Operator.DEC
        super().__init__(op, reg)

    def dry_run(self, regmap : TypeRegmap) -> Expr | None:
        assert isinstance(self.left, Reg) \
            or isinstance(self.left, Direct) \
            or isinstance(self.left, Deref)

        if isinstance(self.left, Reg):
            regmap[self.left] = Expr(SIGNS[self.op], regmap[self.left], Expr(1))
        elif isinstance(self.left, Direct):
            h, l, i = self.left.value
            assert i == 0

            regmap[l] = Expr(SIGNS[self.op], regmap[l], Expr(1))
        else: # Deref
            raise Exception("unimplemeneted")
        return None


class InstInc(InstIncDec):
    def __init__(self, reg: OpdType):
        super().__init__(Operator.INC, reg)


class InstDec(InstIncDec):
    def __init__(self, reg: OpdType):
        super().__init__(Operator.DEC, reg)


class InstAddRegSP(InstALU8bit):
    def __init__(self, r8: int):
        super().__init__(Operator.ADD, operand=r8)
