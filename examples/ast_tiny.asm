SECTION "The thing", ROM0[$100]
	nop
	jp start
	
SECTION "The begining", ROM0[$120]

start:
	ld a, $77
	ld [$CAFE], a

	ld a, [$BAB0]
	inc a
	ld [$BAB1], a

	ld a, [$CEDE]
	inc a
	ld [$CEDE], a


	ld a, [$CAFE]
	ld b, a
	ld a, [$ABBA]
	ld c, a

	push bc
	pop de

	ld a, d
	ld [$ABBA], a
	ld a, e
	ld [$CAFE], a

inf:
	nop
	jr inf
