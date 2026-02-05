SECTION "entry", ROM0[$100]
	nop
	jp main

SECTION "the main", ROM0[$200]
main:
	ld a, $44
	ld [$BABA], a
	xor a
	ld a, [$BABA]
	cp a, $10
	jr c, out_of_range
	cp a, $20
	REPT 10
	inc d
	ENDR
	jr nc, out_of_range
	add a, $10
	ld [$BABA], a
	out_of_range:

	ld a, $0
	ld [$CAFE], a

proc:
	ld a, [$CAFE]
	inc a
	ld [$CAFE], a
	jr proc

nop
REPT 30
dw $a11a
ENDR
