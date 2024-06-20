;--------------------------------------------------------
; File Created by SDCC : free open source ISO C Compiler 
; Version 4.4.1 #14880 (Linux)
;--------------------------------------------------------
	.module rel
	.optsdcc -mstm8
	
;--------------------------------------------------------
; Public variables in this module
;--------------------------------------------------------
	.globl _call_function_expected_by_module
	.globl _function_expected_by_module
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area DATA
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area INITIALIZED
;--------------------------------------------------------
; absolute external ram data
;--------------------------------------------------------
	.area DABS (ABS)

; default segment ordering for linker
	.area HOME
	.area GSINIT
	.area GSFINAL
	.area CONST
	.area INITIALIZER
	.area CODE

;--------------------------------------------------------
; global & static initialisations
;--------------------------------------------------------
	.area HOME
	.area GSINIT
	.area GSFINAL
	.area GSINIT
;--------------------------------------------------------
; Home
;--------------------------------------------------------
	.area HOME
	.area HOME
;--------------------------------------------------------
; code
;--------------------------------------------------------
	.area CODE
;	rel.c: 4: void call_function_expected_by_module(void) {
;	-----------------------------------------
;	 function call_function_expected_by_module
;	-----------------------------------------
_call_function_expected_by_module:
	sub	sp, #2
;	rel.c: 5: for (int i = 0; i < CONSTANT_EXPECTED_BY_MODULE; i++) {
	clrw	x
00103$:
	ldw	y, _CONSTANT_EXPECTED_BY_MODULE+0
	ldw	(0x01, sp), y
	cpw	x, (0x01, sp)
	jrsge	00105$
;	rel.c: 6: function_expected_by_module();
	pushw	x
	call	_function_expected_by_module
	popw	x
;	rel.c: 5: for (int i = 0; i < CONSTANT_EXPECTED_BY_MODULE; i++) {
	incw	x
	jra	00103$
00105$:
;	rel.c: 8: }
	addw	sp, #2
	ret
	.area CODE
	.area CONST
	.area INITIALIZER
	.area CABS (ABS)
