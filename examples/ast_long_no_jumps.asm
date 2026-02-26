SECTION "The thing", ROM0[$100]
	nop
	jp start
	
SECTION "The begining", ROM0[$120]

start:
	ld a, $77
	xor 8
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

	ld a, [$f000]
	ld b, a
	ld a, [$f001]
	and b
	ld [$f002], a
	sla a
	ld [$f003], a
	cpl
	ld [$f004], a
	sub a, b
	ld [$f005], a

	ld hl, $f000
	db 0x34 ; inc (hl)
	db 0x35 ; dec (hl)
	
inf:
	nop
	jr inf
