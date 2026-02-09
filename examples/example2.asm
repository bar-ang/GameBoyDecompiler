SECTION "entry", ROM0[$100]
	nop
	jp main

SECTION "the main", ROM0[$200]
main:

	ld a, 5
	ld [$FAFA], a
	sub a, 8
	jr nc, nothing
	ld [$F0F0], a
nothing:

proc:
	ld a, $44
	ld [$4f4f], a

oopsy:
	inc a
	inc b
	inc c
	jr nc, oopsy

	jr proc

REPT 20
dw $a11a
ENDR
