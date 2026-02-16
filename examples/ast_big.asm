SECTION "The thing", ROM0[$100]
	nop
	jp start
	
SECTION "The begining", ROM0[$120]

start:

; opened IF
	ld a, [$f000]
	cp a, 5
	jp c,  too_small
	inc a
	and a, $f
too_small:
	ld [$f001], a

; closed IF
	ld a, [$b000]
	and a
	jp nz, skip
	ld a, [$b001]
	ld [$b002], a
skip:
	ld a, [$b900]
	ld [$b901], a


inf:
	nop
	jr inf
