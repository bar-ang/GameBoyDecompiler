SECTION "The thing", ROM0[$100]
	nop
	jp start
	
SECTION "The begining", ROM0[$120]

start:

	ld a, [$1]
	jr nz, elseclause

	ld [$2], a

	jr after
elseclause:
	
	ld [$3], a
after:
	ld a, [$f]
	inc a
	ld [$f], a

inf:
	jr inf
