;--------------------------------------------------------
; File Created by SDCC : free open source ISO C Compiler 
; Version 4.4.1 #14880 (Linux)
;--------------------------------------------------------
	.module main
	.optsdcc -mstm8
	
;--------------------------------------------------------
; Public variables in this module
;--------------------------------------------------------
	.globl _alternative_main
	.globl _alternative_main_sub
	.globl _main
	.globl __main
	.globl _NON_EMPTY_IRQ_HANDLER_sub
	.globl _NON_EMPTY_IRQ_HANDLER
	.globl _EMPTY_IRQ_HANDLER
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area DATA
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area INITIALIZED
;--------------------------------------------------------
; Stack segment in internal ram
;--------------------------------------------------------
	.area SSEG
__start__stack:
	.ds	1

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
; interrupt vector
;--------------------------------------------------------
	.area HOME
__interrupt_vect:
	int s_GSINIT ; reset
	int 0x000000 ; trap
	int _NON_EMPTY_IRQ_HANDLER ; int0
	int _EMPTY_IRQ_HANDLER ; int1
;--------------------------------------------------------
; global & static initialisations
;--------------------------------------------------------
	.area HOME
	.area GSINIT
	.area GSFINAL
	.area GSINIT
	call	___sdcc_external_startup
	tnz	a
	jreq	__sdcc_init_data
	jp	__sdcc_program_startup
__sdcc_init_data:
; stm8_genXINIT() start
	ldw x, #l_DATA
	jreq	00002$
00001$:
	clr (s_DATA - 1, x)
	decw x
	jrne	00001$
00002$:
	ldw	x, #l_INITIALIZER
	jreq	00004$
00003$:
	ld	a, (s_INITIALIZER - 1, x)
	ld	(s_INITIALIZED - 1, x), a
	decw	x
	jrne	00003$
00004$:
; stm8_genXINIT() end
	.area GSFINAL
	jp	__sdcc_program_startup
;--------------------------------------------------------
; Home
;--------------------------------------------------------
	.area HOME
	.area HOME
__sdcc_program_startup:
	jp	_main
;	return from main will return to caller
;--------------------------------------------------------
; code
;--------------------------------------------------------
	.area XDDCODE
;	main.c: 4: void NON_EMPTY_IRQ_HANDLER_sub(void) {
;	-----------------------------------------
;	 function NON_EMPTY_IRQ_HANDLER_sub
;	-----------------------------------------
_NON_EMPTY_IRQ_HANDLER_sub:
;	main.c: 5: __asm__("nop");
	nop
;	main.c: 6: }
	ret
;	main.c: 8: void NON_EMPTY_IRQ_HANDLER() __interrupt(0) {
;	-----------------------------------------
;	 function NON_EMPTY_IRQ_HANDLER
;	-----------------------------------------
_NON_EMPTY_IRQ_HANDLER:
	clr	a
	div	x, a
;	main.c: 9: NON_EMPTY_IRQ_HANDLER_sub();
	call	_NON_EMPTY_IRQ_HANDLER_sub
;	main.c: 10: }
	iret
;	main.c: 12: void EMPTY_IRQ_HANDLER() __interrupt(1) {
;	-----------------------------------------
;	 function EMPTY_IRQ_HANDLER
;	-----------------------------------------
_EMPTY_IRQ_HANDLER:
;	main.c: 13: }
	iret
;	main.c: 17: void main(void) {
;	-----------------------------------------
;	 function main
;	-----------------------------------------
_main:
;	main.c: 18: _main();
;	main.c: 19: }
	jp	__main
;	main.c: 21: void alternative_main_sub(void) {
;	-----------------------------------------
;	 function alternative_main_sub
;	-----------------------------------------
_alternative_main_sub:
;	main.c: 22: _main();
;	main.c: 23: }
	jp	__main
;	main.c: 25: void alternative_main(void) {
;	-----------------------------------------
;	 function alternative_main
;	-----------------------------------------
_alternative_main:
;	main.c: 26: alternative_main_sub();
;	main.c: 27: }
	jp	_alternative_main_sub
	.area XDDCODE
	.area XDDCONST
	.area INITIALIZER
	.area CABS (ABS)
