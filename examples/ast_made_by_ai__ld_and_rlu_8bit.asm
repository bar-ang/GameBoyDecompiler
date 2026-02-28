; --------------------------------------------------
; Setup WRAM addresses
; --------------------------------------------------
DEF RAM_A      EQU $C000
DEF RAM_B      EQU $C001
DEF RAM_SUM    EQU $C002
DEF RAM_RESULT EQU $C003
DEF RAM_FLAGS  EQU $C004

SECTION "The thing", ROM0[$100]
	nop
	jp start
	
SECTION "MeaningfulTest", ROM0[$200]

start:
; --------------------------------------------------
; Initialize values in RAM
; --------------------------------------------------

    ld   hl, RAM_A
    ld   [hl], $14        ; RAM_A = 0x14 (20)

    inc  hl
    ld   [hl], $22        ; RAM_B = 0x22 (34)

; --------------------------------------------------
; Load A = RAM_A
; --------------------------------------------------

    ld   hl, RAM_A
    ld   a, [hl]

; --------------------------------------------------
; Add RAM_B
; --------------------------------------------------

    ld   hl, RAM_B
    add  a, [hl]          ; A = A + RAM_B

    ld   hl, RAM_SUM
    ld   [hl], a          ; store sum

; --------------------------------------------------
; Multiply by 2 (shift left)
; --------------------------------------------------

    sla  a                ; A = A * 2

; --------------------------------------------------
; XOR with constant
; --------------------------------------------------

    xor  $AA

    ld   hl, RAM_RESULT
    ld   [hl], a          ; store final result

; --------------------------------------------------
; Bit tests and flag storage
; --------------------------------------------------

    bit  7, a             ; test MSB

    ld   hl, RAM_FLAGS
    ld   b, 0
    rl   b                ; move carry into bit 0
    ld   [hl], b

; --------------------------------------------------
; Demonstrate stack usage
; --------------------------------------------------

    ld   sp, $D000

    ld   bc, $1234
    push bc
    xor  a
    pop  de               ; DE now 0x1234

    ld   hl, $C010
    ld   [hl], d
    inc  hl
    ld   [hl], e

; --------------------------------------------------
; High RAM test
; --------------------------------------------------

    ld   a, $55
    ldh  [$FF80], a         ; write to HRAM $FF80
    ldh  a, [$FF80]

; --------------------------------------------------
; Misc arithmetic
; --------------------------------------------------

    inc  a
    dec  a
    cpl
    scf
    ccf
    daa

; --------------------------------------------------
; Halt CPU (not flow control)
; --------------------------------------------------

    ld a, [$dddd]
    ld b, a
    inc a
    ld c, a
    push bc
    pop de
    ld a, d
    ld [$ddde], a
    ld a, e
    ld [$dddf], a

    halt

done:
    jr done
