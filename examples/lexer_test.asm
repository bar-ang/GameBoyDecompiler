SECTION "Full CPU Test", ROM0

; ------------------------------
; Load/Store instructions
; ------------------------------
LD A, $12
LD B, $34
LD C, $56
LD D, $78
LD E, $9A
LD H, $BC
LD L, $DE

;LD (HL), A
;LD A, (HL)
;LD (BC), A
;LD (DE), A
;LD A, (BC)
;LD A, (DE)
;LD (HL+), A
;LD (HL-), A
;LD (C), A        ; LD (0xFF00 + C), A
;LD A, (C)

LD SP, $FFF0
LD HL, $1234
;LD (HL), B

; ------------------------------
; Immediate loads
; ------------------------------
LD A, $0F
LD B, $1F
LD C, $2F
LD D, $3F
LD E, $4F
LD H, $5F
LD L, $6F

; ------------------------------
; Arithmetic instructions
; ------------------------------
ADD A, B
ADC A, C
SUB D
SBC A, E
AND H
OR L
XOR A
CP $80
INC A
DEC B
INC C
DEC D
INC E
DEC H
INC L
DEC A
ADD HL, BC
ADD HL, DE
ADD HL, HL
ADD HL, SP
ADD SP, $10
;SUB HL, BC      ; invalid, will comment out
; ------------------------------
; Rotates/Shifts
; ------------------------------
RLCA
RLA
RRCA
RRA
RLC B
RRC C
RL D
RR E
SLA H
SRA L
SWAP A
SRL B

; ------------------------------
; Jumps / Calls / Returns
; ------------------------------
JP $1234
JP NZ, $2345
JP Z, $3456
JP NC, $4567
JP C, $5678
JR $05
JR NZ, $06
JR Z, $07
JR NC, $08
JR C, $09
CALL $1234
CALL NZ, $2345
CALL Z, $3456
CALL NC, $4567
CALL C, $5678
RET
RET NZ
RET Z
RET NC
RET C
RETI
RST $00
RST $08
RST $10
RST $18
RST $20
RST $28
RST $30
RST $38

; ------------------------------
; Bit operations (CB prefix)
; ------------------------------
PREFIX_CB:
    RLC B
    RRC C
    BIT 7, H
    SET 3, D
    RES 2, E

; ------------------------------
; Misc / Stack
; ------------------------------
PUSH BC
PUSH DE
PUSH HL
PUSH AF
POP BC
POP DE
POP HL
POP AF
NOP
HALT
STOP
DI
EI
CPL
CCF
SCF

; ------------------------------
; Infinite loop at end
; ------------------------------
Loop:
    JR Loop










