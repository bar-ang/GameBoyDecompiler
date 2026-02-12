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


inf:
	jr inf
