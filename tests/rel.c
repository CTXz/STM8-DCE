extern const int CONSTANT_EXPECTED_BY_MODULE;
extern void function_expected_by_module(void);

void call_function_expected_by_module(void) {
    for (int i = 0; i < CONSTANT_EXPECTED_BY_MODULE; i++) {
        function_expected_by_module();
    }
}