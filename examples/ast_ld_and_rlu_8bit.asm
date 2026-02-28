SECTION "The thing", ROM0[$100]
	nop
	jp start
	
SECTION "The begining", ROM0[$120]

start:
	ld a, [$cafe]
	ld b, a
	inc a
	xor b
	ld [$cafe], a

	ld a, [$baba]
	ld b, a
	ld c, a
	sla b
	xor a
	ld [$a000], a
	ld a, b
	ld [$baba], a


inf:
	nop
	jr inf
