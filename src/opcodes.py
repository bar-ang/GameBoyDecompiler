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






############## FLOW CONTROL COMMANDS #############

# --- JUMP COMMANDS ---
JR_R8           = 0x18      # JR r8
JR_NZ_R8        = 0x20      # JR NZ,r8
JR_Z_R8         = 0x28      # JR Z,r8
JR_NC_R8        = 0x30      # JR NC,r8
JR_C_R8         = 0x38      # JR C,r8

JP_NZ_A16       = 0xC2      # JP NZ,a16
JP_A16          = 0xC3      # JP a16
JP_Z_A16        = 0xCA      # JP Z,a16
JP_NC_A16       = 0xD2      # JP NC,a16
JP_C_A16        = 0xDA      # JP C,a16
JP_HL           = 0xE9      # JP (HL)

# --- CALL COMMANDS ---
CALL_NZ_A16     = 0xC4      # CALL NZ,a16
CALL_Z_A16      = 0xCC      # CALL Z,a16
CALL_A16        = 0xCD      # CALL a16
CALL_NC_A16     = 0xD4      # CALL NC,a16
CALL_C_A16      = 0xDC      # CALL C,a16

# --- RETURN COMMANDS ---
RET_NZ          = 0xC0      # RET NZ
RET_Z           = 0xC8      # RET Z
RET             = 0xC9      # RET
RETI            = 0xD9      # RETI
RET_NC          = 0xD0      # RET NC
RET_C           = 0xD8      # RET C

# --- RESTART COMMANDS ---
RST_00H         = 0xC7      # RST 00H
RST_08H         = 0xCF      # RST 08H
RST_10H         = 0xD7      # RST 10H
RST_18H         = 0xDF      # RST 18H
RST_20H         = 0xE7      # RST 20H
RST_28H         = 0xEF      # RST 28H
RST_30H         = 0xF7      # RST 30H
RST_38H         = 0xFF      # RST 38H




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

HL_OP_GROUP = {
    # load from (HL)
    LD_A_HL_INC, LD_A_HL_DEC, LD_B_HL, LD_C_HL,
    LD_D_HL, LD_E_HL, LD_H_HL, LD_L_HL, LD_A_HL,

    # store to (HL)
    ST_HL_INC_A, ST_HL_DEC_A, ST_HL_B, ST_HL_C,
    ST_HL_D, ST_HL_E, ST_HL_H, ST_HL_L, ST_HL_A,
}


JR_COMMANDS = {
    JR_R8, JR_NZ_R8, JR_Z_R8, JR_NC_R8, JR_C_R8
}

JP_COMMANDS = {
    JP_NZ_A16, JP_A16, JP_Z_A16, JP_NC_A16,
    JP_C_A16, JP_HL
}

CALL_COMMANDS = {
    CALL_NZ_A16, CALL_Z_A16, CALL_A16,
    CALL_NC_A16, CALL_C_A16
}

RET_COMMANDS = {
    RET_NZ, RET_Z, RET, RETI, RET_NC, RET_C
}

RST_COMMANDS = {
    RST_00H, RST_08H, RST_10H, RST_18H,
    RST_20H, RST_28H, RST_30H, RST_38H
}
