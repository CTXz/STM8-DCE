asm:
	mkdir -p build/asm
	sdcc -o build/asm/main.asm -mstm8 --out-fmt-elf -DSTM8S103 -S main.c
	sdcc -o build/asm/_main.asm -mstm8 --out-fmt-elf -DSTM8S103 -S _main.c
	sdcc -o build/asm/extra.asm -mstm8 --out-fmt-elf -DSTM8S103 -S extra.c

asm_custom_codeconstseg:
	mkdir -p build/asm_custom_codeconstseg
	sdcc -o build/asm_custom_codeconstseg/main.asm -mstm8 --codeseg XDDCODE --constseg XDDCONST --out-fmt-elf -DSTM8S103 -S main.c
	sdcc -o build/asm_custom_codeconstseg/_main.asm -mstm8 --codeseg XDDCODE --constseg XDDCONST --out-fmt-elf -DSTM8S103 -S _main.c
	sdcc -o build/asm_custom_codeconstseg/extra.asm -mstm8 --codeseg XDDCODE --constseg XDDCONST --out-fmt-elf -DSTM8S103 -S extra.c

rel:
	mkdir -p build/obj
	sdcc -o build/obj/rel.rel -mstm8 --out-fmt-elf -DSTM8S103 -c rel.c
	sdcc -o build/obj/main.rel -mstm8 --out-fmt-elf -DSTM8S103 -c main.c

lib: rel
	sdar -rcs build/obj/lib.lib build/obj/rel.rel build/obj/main.rel

clean:
	rm -rf build

.PHONY: all clean