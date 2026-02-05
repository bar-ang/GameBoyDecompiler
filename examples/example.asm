SECTION "nothing", ROM0[0]
	REPT $100/2
	dw $1aa1
	ENDR

SECTION "main", ROM0[$100]
	ld a, [$CAFE]
	ld b, a
	add a, 5
	xor b
	ld [$BEEF], a
	call Gerbil

process:
	jr process

SECTION "avocado", ROM0[$192]
	ld a, $bb
	ld [$DEAF], a
	call Gerbil


SECTION "Mr X", ROMX[$4020]

	ld a, $55
	ld b, a
	call Gerbil

	REPT 10
		push af
		pop af
	ENDR

Gerbil:
	ld a, [$6543]
	inc a
	ld [$6543], a
	ret



SECTION "an hellenic section", WRAM0[$c100]
	wFoofoo: db
	;wBamba: ds 8, 2
