;--------------------------------------------------------
; File Created by SDCC : free open source ISO C Compiler 
; Version 4.4.1 #14880 (Linux)
;--------------------------------------------------------
	.module _main
	.optsdcc -mstm8
	
;--------------------------------------------------------
; Public variables in this module
;--------------------------------------------------------
	.globl _EXCLUDED_CONSTANT
	.globl _CONSTANT_EXPECTED_BY_MODULE
	.globl _USED_CONSTANT
	.globl _UNUSED_CONSTANT
	.globl __main
	.globl _function_expected_by_module
	.globl _function_expected_by_module_sub
	.globl _excluded_function
	.globl _excluded_function_sub
	.globl _function_used_by_ptr
	.globl _function_used_by_ptr_sub
	.globl _used_function
	.globl _used_function_sub
	.globl _unused_function
	.globl _call_function_expected_by_module
	.globl _external_function_ptr
	.globl _external_const_array_ptr
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area DATA
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area INITIALIZED
_external_const_array_ptr::
	.ds 2
_external_function_ptr::
	.ds 2
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
	.area XDDCODE
;	_main.c: 18: void unused_function(void) {
;	-----------------------------------------
;	 function unused_function
;	-----------------------------------------
_unused_function:
	sub	sp, #2
;	_main.c: 19: for (int i = 0; i < UNUSED_CONSTANT; i++) {
	clrw	x
00103$:
	ldw	y, _UNUSED_CONSTANT+0
	ldw	(0x01, sp), y
	cpw	x, (0x01, sp)
	jrsge	00105$
;	_main.c: 20: __asm__("nop");
	nop
;	_main.c: 19: for (int i = 0; i < UNUSED_CONSTANT; i++) {
	incw	x
	jra	00103$
00105$:
;	_main.c: 22: }
	addw	sp, #2
	ret
;	_main.c: 24: void used_function_sub(void) {
;	-----------------------------------------
;	 function used_function_sub
;	-----------------------------------------
_used_function_sub:
	sub	sp, #2
;	_main.c: 25: for (int i = 0; i < USED_CONSTANT; i++) {
	clrw	x
00103$:
	ldw	y, _USED_CONSTANT+0
	ldw	(0x01, sp), y
	cpw	x, (0x01, sp)
	jrsge	00105$
;	_main.c: 26: __asm__("nop");
	nop
;	_main.c: 25: for (int i = 0; i < USED_CONSTANT; i++) {
	incw	x
	jra	00103$
00105$:
;	_main.c: 28: }
	addw	sp, #2
	ret
;	_main.c: 30: void used_function(void) {
;	-----------------------------------------
;	 function used_function
;	-----------------------------------------
_used_function:
;	_main.c: 31: used_function_sub();
;	_main.c: 32: }
	jp	_used_function_sub
;	_main.c: 34: void function_used_by_ptr_sub(void) {
;	-----------------------------------------
;	 function function_used_by_ptr_sub
;	-----------------------------------------
_function_used_by_ptr_sub:
;	_main.c: 35: __asm__("nop");
	nop
;	_main.c: 36: }
	ret
;	_main.c: 38: void function_used_by_ptr(void) {
;	-----------------------------------------
;	 function function_used_by_ptr
;	-----------------------------------------
_function_used_by_ptr:
;	_main.c: 39: function_used_by_ptr_sub();
;	_main.c: 40: }
	jp	_function_used_by_ptr_sub
;	_main.c: 42: void excluded_function_sub(void) {
;	-----------------------------------------
;	 function excluded_function_sub
;	-----------------------------------------
_excluded_function_sub:
;	_main.c: 43: __asm__("nop");
	nop
;	_main.c: 44: }
	ret
;	_main.c: 46: void excluded_function(void) {
;	-----------------------------------------
;	 function excluded_function
;	-----------------------------------------
_excluded_function:
;	_main.c: 47: excluded_function_sub();
;	_main.c: 48: }
	jp	_excluded_function_sub
;	_main.c: 50: static void local_excluded_function_sub(void) {
;	-----------------------------------------
;	 function local_excluded_function_sub
;	-----------------------------------------
_local_excluded_function_sub:
;	_main.c: 51: __asm__("nop");
	nop
;	_main.c: 52: }
	ret
;	_main.c: 54: static void local_excluded_function(void) {
;	-----------------------------------------
;	 function local_excluded_function
;	-----------------------------------------
_local_excluded_function:
;	_main.c: 55: local_excluded_function_sub();
;	_main.c: 56: }
	jp	_local_excluded_function_sub
;	_main.c: 58: void function_expected_by_module_sub(void) {
;	-----------------------------------------
;	 function function_expected_by_module_sub
;	-----------------------------------------
_function_expected_by_module_sub:
;	_main.c: 59: __asm__("nop");
	nop
;	_main.c: 60: }
	ret
;	_main.c: 62: void function_expected_by_module(void) {
;	-----------------------------------------
;	 function function_expected_by_module
;	-----------------------------------------
_function_expected_by_module:
;	_main.c: 63: function_expected_by_module_sub();
;	_main.c: 64: }
	jp	_function_expected_by_module_sub
;	_main.c: 66: static void local_function_sub(void) {
;	-----------------------------------------
;	 function local_function_sub
;	-----------------------------------------
_local_function_sub:
	sub	sp, #2
;	_main.c: 67: for (int i = 0; i < LOCAL_CONSTANT; i++) {
	clrw	x
00103$:
	ldw	y, _LOCAL_CONSTANT+0
	ldw	(0x01, sp), y
	cpw	x, (0x01, sp)
	jrsge	00105$
;	_main.c: 68: __asm__("nop");
	nop
;	_main.c: 67: for (int i = 0; i < LOCAL_CONSTANT; i++) {
	incw	x
	jra	00103$
00105$:
;	_main.c: 69: }}
	addw	sp, #2
	ret
;	_main.c: 71: static void local_function(void) {
;	-----------------------------------------
;	 function local_function
;	-----------------------------------------
_local_function:
;	_main.c: 72: local_function_sub();
;	_main.c: 73: }
	jp	_local_function_sub
;	_main.c: 75: void _main(void) {
;	-----------------------------------------
;	 function _main
;	-----------------------------------------
__main:
	push	a
;	_main.c: 76: used_function();
	call	_used_function
;	_main.c: 77: local_function();
	call	_local_function
;	_main.c: 78: call_function_expected_by_module();
	call	_call_function_expected_by_module
;	_main.c: 80: void (*function_ptr)(void) = &function_used_by_ptr;
	ldw	x, #(_function_used_by_ptr+0)
;	_main.c: 81: function_ptr();
	call	(x)
;	_main.c: 83: for (uint8_t i = 0; i < external_const_array_ptr[1]; i++) {
	clr	(0x01, sp)
00103$:
	ldw	x, _external_const_array_ptr+0
	ld	a, (0x1, x)
	cp	a, (0x01, sp)
	jrule	00105$
;	_main.c: 84: external_function_ptr();
	ldw	x, _external_function_ptr+0
	call	(x)
;	_main.c: 83: for (uint8_t i = 0; i < external_const_array_ptr[1]; i++) {
	inc	(0x01, sp)
	jra	00103$
00105$:
;	_main.c: 86: }
	pop	a
	ret
	.area XDDCODE
	.area XDDCONST
_UNUSED_CONSTANT:
	.dw #0x007b
_USED_CONSTANT:
	.dw #0x0141
_CONSTANT_EXPECTED_BY_MODULE:
	.dw #0x01c8
_EXCLUDED_CONSTANT:
	.dw #0x028e
_LOCAL_CONSTANT:
	.dw #0x0315
_LOCAL_EXCLUDED_CONSTANT:
	.dw #0x03db
	.area INITIALIZER
__xinit__external_const_array_ptr:
	.dw _EXTERNAL_CONST_ARRAY
__xinit__external_function_ptr:
	.dw _external_function
	.area CABS (ABS)
