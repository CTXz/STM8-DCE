void NON_EMPTY_IRQ_HANDLER(void) __interrupt(0);
void EMPTY_IRQ_HANDLER(void) __interrupt(1); 

void NON_EMPTY_IRQ_HANDLER_sub(void) {
    __asm__("nop");
}

void NON_EMPTY_IRQ_HANDLER(void) __interrupt(0) {
    NON_EMPTY_IRQ_HANDLER_sub();
}

void EMPTY_IRQ_HANDLER(void) __interrupt(1) {
}

void _main(void);

void main(void) {
    _main();
}

void alternative_main_sub(void) {
    _main();
}

void alternative_main(void) {
    alternative_main_sub();
}