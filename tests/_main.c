#include <stdint.h>

/* SDCC v4.0 and older does not automatically "pull" the module containing the main function
 * Referencing the main function here fixes that
 * See https://github.com/tenbaht/sduino/issues/76
 */
#ifdef EXT
void main(void);
void (*dummy_variable) (void) = main;
#endif

volatile const int UNUSED_CONSTANT = 123;
volatile const int USED_CONSTANT = 321;
volatile const int CONSTANT_EXPECTED_BY_MODULE = 456;
volatile const int EXCLUDED_CONSTANT = 654;
volatile static const int LOCAL_CONSTANT = 789;
volatile static const int LOCAL_EXCLUDED_CONSTANT = 987;

extern const uint8_t EXTERNAL_CONST_ARRAY[];
void external_function(void);

void call_function_expected_by_module(void);

uint8_t *external_const_array_ptr = EXTERNAL_CONST_ARRAY;
void (*external_function_ptr)(void) = &external_function;

void unused_function(void) {
    for (int i = 0; i < UNUSED_CONSTANT; i++) {
        __asm__("nop");
    }
}

void unused_function_with_fptr(void) {
    void (*function_ptr)(void) = &unused_function;
    for (int i = 0; i < UNUSED_CONSTANT; i++) {
        function_ptr();
    }
}

void used_function_sub(void) {
    for (int i = 0; i < USED_CONSTANT; i++) {
        __asm__("nop");
    }
}

void used_function(void) {
    used_function_sub();
}

void function_used_by_ptr_sub(void) {
    __asm__("nop");
}

void function_used_by_ptr(void) {
    function_used_by_ptr_sub();
}

void excluded_function_sub(void) {
    __asm__("nop");
}

void excluded_function(void) {
    excluded_function_sub();
}

static void local_excluded_function_sub(void) {
    __asm__("nop");
}

static void local_excluded_function(void) {
    local_excluded_function_sub();
}

void function_expected_by_module_sub(void) {
    __asm__("nop");
}

void function_expected_by_module(void) {
    function_expected_by_module_sub();
}

static void local_function_sub(void) {
    for (int i = 0; i < LOCAL_CONSTANT; i++) {
        __asm__("nop");
    }}

static void local_function(void) {
    local_function_sub();
}

void recursive_function(void) {
    recursive_function();
}

void _main(void) {
    used_function();
    local_function();

#ifdef EXT
    call_function_expected_by_module();
#endif

    void (*function_ptr)(void) = &function_used_by_ptr;
    function_ptr();

    for (uint8_t i = 0; i < external_const_array_ptr[1]; i++) {
        external_function_ptr();
    }

    recursive_function();
}
