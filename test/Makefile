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
	sdcc -o build/obj/main.rel -mstm8 --out-fmt-elf -DSTM8S103 -DEXT -c main.c

asm_rel_lib:
	mkdir -p build/asm_rel_lib
	sdcc -o build/asm_rel_lib/main.asm -mstm8 --out-fmt-elf -DSTM8S103 -S main.c
	sdcc -o build/asm_rel_lib/_main.asm -mstm8 --out-fmt-elf -DSTM8S103 -DEXT -S _main.c
	sdcc -o build/asm_rel_lib/extra.asm -mstm8 --out-fmt-elf -DSTM8S103 -S extra.c

lib: rel asm_rel_lib
	sdar -rcs build/obj/lib.lib build/obj/rel.rel build/obj/main.rel

elf_test:
	mkdir -p build/out
	sdasstm8 -plosg -ff -o build/out/main.rel build/dce/main.asm
	sdasstm8 -plosg -ff -o build/out/_main.rel build/dce/_main.asm
	sdasstm8 -plosg -ff -o build/out/extra.rel build/dce/extra.asm
	sdcc -o build/out/main.elf -mstm8 --out-fmt-elf -DSTM8S103 build/out/main.rel build/out/_main.rel build/out/extra.rel
	rm -rf build/out

elf_rel_test: rel
	mkdir -p build/out
	sdasstm8 -plosg -ff -o build/out/main.rel build/dce_rel_lib/main.asm
	sdasstm8 -plosg -ff -o build/out/_main.rel build/dce_rel_lib/_main.asm
	sdasstm8 -plosg -ff -o build/out/extra.rel build/dce_rel_lib/extra.asm
	sdcc -o build/out/main.elf -mstm8 --out-fmt-elf -DSTM8S103 build/out/main.rel build/out/_main.rel build/out/extra.rel build/obj/rel.rel
	rm -rf build/out

elf_custom_codeconstseg_test: asm_custom_codeconstseg
	mkdir -p build/out
	sdasstm8 -plosg -ff -o build/out/main.rel build/asm_custom_codeconstseg/main.asm
	sdasstm8 -plosg -ff -o build/out/_main.rel build/asm_custom_codeconstseg/_main.asm
	sdasstm8 -plosg -ff -o build/out/extra.rel build/asm_custom_codeconstseg/extra.asm
	sdcc -o build/out/main.elf -mstm8 --out-fmt-elf -DSTM8S103 build/out/main.rel build/out/_main.rel build/out/extra.rel
	rm -rf build/out

clean:
	rm -rf build

.PHONY: all clean