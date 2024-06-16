# STM8DCE Example <!-- omit in toc -->

This example demonstrates the STM8DCE tool on a simply blinky project targeting the STM8S103 microcontroller. To truly showcase the effectiveness of the dead code elimination, this example builds **all** STM8S103-compatible modules from the STM8S Standard Peripheral Library. Without DCE, this would undoubtedly result in a binary size that exceeds the STM8S103's 8KB flash limit.

## Table of Contents <!-- omit in toc -->
- [Pre-requisites](#pre-requisites)
- [Building](#building)
  - [Generating the Assembly Files](#generating-the-assembly-files)
  - [Applying Dead Code Elimination with STM8DCE](#applying-dead-code-elimination-with-stm8dce)
  - [Assembling the optimized assembly files to object files](#assembling-the-optimized-assembly-files-to-object-files)
  - [Linking the object files to an ELF file](#linking-the-object-files-to-an-elf-file)
  - [Generating an ihx file from the ELF file](#generating-an-ihx-file-from-the-elf-file)
  - [Checking the size](#checking-the-size)
  - [Flashing the ihx file to the STM8S103](#flashing-the-ihx-file-to-the-stm8s103)
  - [Makefile](#makefile)


## Pre-requisites

Ensure that you have the following tools installed:

- [SDCC](http://sdcc.sourceforge.net/) (4.4.1 is recommended at the time of writing)
- [stm8-binutils-gdb](https://stm8-binutils-gdb.sourceforge.io/) for objcopy to generate a ihx file from the elf file
- [stm8flash](https://github.com/vdudouyt/stm8flash) for flashing the ihx file to the STM8S103

and obviously the STM8DCE tool which can be found at the top of this repository!

## Building

We'll now go through all manual steps to build the project. The `Makefile` in this repository automates these steps, but it is advantageous to understand every step should you wish to integrate STM8DCE into your own build environment.

### Generating the Assembly Files

Since the STM8DCE tool operates on assembly files, we need to generate these from the C files. SDCC provides the `-S` flag for this purpose. The following command will generate the assembly files for all STM8S103 relevant SPL modules, as well as the source files of this project:

Create a build directory:
```bash
mkdir -p build/asm/
```

Standard Peripheral Library:
```bash
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_adc1.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_adc1.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_awu.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_awu.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_beep.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_beep.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_clk.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_clk.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_exti.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_exti.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_flash.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_flash.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_gpio.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_gpio.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_i2c.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_i2c.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_itc.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_itc.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_iwdg.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_iwdg.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_rst.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_rst.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_spi.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_spi.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_tim1.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_tim1.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_tim2.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_tim2.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_uart1.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_uart1.asm && \
sdcc lib/STM8S_StdPeriph_Driver/src/stm8s_wwdg.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_wwdg.asm
```

Project Source Files:
```bash
sdcc src/main.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/main.asm && \
sdcc src/stm8s_it.c -mstm8 --out-fmt-elf -Iinclude/ -Isrc/ -Ilib/STM8S_StdPeriph_Driver/inc -DSTM8S103 -S -o build/asm/stm8s_it.asm
```

This should generate the following assembly files in the `build/asm` directory:
```
$ ls build/asm
main.asm        stm8s_awu.asm   stm8s_clk.asm   stm8s_flash.asm  stm8s_i2c.asm  stm8s_itc.asm   stm8s_rst.asm  stm8s_tim1.asm  stm8s_uart1.asm
stm8s_adc1.asm  stm8s_beep.asm  stm8s_exti.asm  stm8s_gpio.asm   stm8s_it.asm   stm8s_iwdg.asm  stm8s_spi.asm  stm8s_tim2.asm  stm8s_wwdg.asm
```

### Applying Dead Code Elimination with STM8DCE

Now that we have the assembly files, we can apply the STM8DCE tool to eliminate dead code. First, we'll create a new directory to store the optimized assembly files:

```bash
mkdir -p build/dce/
```

Next, we can run the STM8DCE tool on the assembly files. We'll use the `-v` flag to enable verbose output, which neatly shows which functions and constants were eliminated. Additionally, we will provide the path to the standard library, since some SPL modules may reference it:

```bash
stm8dce -v -o build/dce build/asm/*.asm /path/to/stm8.lib
```

> **Note:** The standard library can typically be found in the `lib` directory of the SDCC installation. On Linux systems, it is usually located at `/usr/share/sdcc/lib/stm8/stm8.lib` or `/usr/local/share/sdcc/lib/stm8/stm8.lib`. Including the standard library is important to ensure that STM8DCE does not eliminate any code that may be expected by the standard library (e.g., `putchar`, `getchar`, etc.). Omitting the standard library here may lead to linker errors, as the tool might remove essential functions used by the standard library.

Here is a truncated output for brevity:

```
Removing Functions:
        _BEEP_DeInit - build/dce/stm8s_beep.asm:57
        _BEEP_Init - build/dce/stm8s_beep.asm:66
        _BEEP_Cmd - build/dce/stm8s_beep.asm:113
        _BEEP_LSICalibrationConfig - build/dce/stm8s_beep.asm:137
        _CLK_DeInit - build/dce/stm8s_clk.asm:78
        _CLK_FastHaltWakeUpCmd - build/dce/stm8s_clk.asm:112
        _CLK_HSECmd - build/dce/stm8s_clk.asm:147
        _CLK_HSICmd - build/dce/stm8s_clk.asm:182
        ...

Removing Constants:
        ___str_0 - build/dce/stm8s_beep.asm:226
        _HSIDivFactor - build/dce/stm8s_clk.asm:1337
        _CLKPrescTable - build/dce/stm8s_clk.asm:1342
        ___str_0 - build/dce/stm8s_clk.asm:1352
        _APR_Array - build/dce/stm8s_awu.asm:300
        _TBR_Array - build/dce/stm8s_awu.asm:318
        ___str_0 - build/dce/stm8s_awu.asm:337
        ___str_0 - build/dce/stm8s_tim2.asm:2090
        ___str_0 - build/dce/stm8s_exti.asm:352
        ...

Detected and removed:
290 unused functions from a total of 315 functions
19 unused constants from a total of 20 constants
```

If you are curious, you can compare the processed assembly files in the `build/dce` directory with the original ones in the `build/asm` directory. You will notice that the eliminated functions and constants have been commented out.

### Assembling the optimized assembly files to object files

The next step is to assemble the optimized assembly files to object files. SDCC provides the `sdasstm8` assembler for this purpose.

We'll first create a new directory to store the object files:
```bash 
mkdir -p build/obj/
```

We then assemble the Standard Peripheral Library:
```bash 
sdasstm8 -plosg -ff -o build/obj/stm8s_adc1.rel build/dce/stm8s_adc1.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_awu.rel build/dce/stm8s_awu.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_beep.rel build/dce/stm8s_beep.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_clk.rel build/dce/stm8s_clk.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_exti.rel build/dce/stm8s_exti.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_flash.rel build/dce/stm8s_flash.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_gpio.rel build/dce/stm8s_gpio.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_i2c.rel build/dce/stm8s_i2c.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_itc.rel build/dce/stm8s_itc.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_iwdg.rel build/dce/stm8s_iwdg.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_rst.rel build/dce/stm8s_rst.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_spi.rel build/dce/stm8s_spi.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_tim1.rel build/dce/stm8s_tim1.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_tim2.rel build/dce/stm8s_tim2.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_uart1.rel build/dce/stm8s_uart1.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_wwdg.rel build/dce/stm8s_wwdg.asm
```

and the project source files:
```bash
sdasstm8 -plosg -ff -o build/obj/main.rel build/dce/main.asm && \
sdasstm8 -plosg -ff -o build/obj/stm8s_it.rel build/dce/stm8s_it.asm
```

The contents of the `build/obj` directory should now look like this:
```
$ ls build/obj
main.lst        stm8s_adc1.sym  stm8s_beep.rel  stm8s_exti.lst   stm8s_flash.sym  stm8s_i2c.rel  stm8s_it.lst    stm8s_iwdg.sym  stm8s_spi.rel   stm8s_tim2.lst   stm8s_uart1.sym
main.rel        stm8s_awu.lst   stm8s_beep.sym  stm8s_exti.rel   stm8s_gpio.lst   stm8s_i2c.sym  stm8s_it.rel    stm8s_rst.lst   stm8s_spi.sym   stm8s_tim2.rel   stm8s_wwdg.lst
main.sym        stm8s_awu.rel   stm8s_clk.lst   stm8s_exti.sym   stm8s_gpio.rel   stm8s_itc.lst  stm8s_it.sym    stm8s_rst.rel   stm8s_tim1.lst  stm8s_tim2.sym   stm8s_wwdg.rel
stm8s_adc1.lst  stm8s_awu.sym   stm8s_clk.rel   stm8s_flash.lst  stm8s_gpio.sym   stm8s_itc.rel  stm8s_iwdg.lst  stm8s_rst.sym   stm8s_tim1.rel  stm8s_uart1.lst  stm8s_wwdg.sym
stm8s_adc1.rel  stm8s_beep.lst  stm8s_clk.sym   stm8s_flash.rel  stm8s_i2c.lst    stm8s_itc.sym  stm8s_iwdg.rel  stm8s_spi.lst   stm8s_tim1.sym  stm8s_uart1.rel
```

### Linking the object files to an ELF file

The next step is to link the object files to an ELF file. This is done using `sdcc`: again. We'll output `blinky.elf` to the `build` directory:
```bash
sdcc -mstm8 --out-fmt-elf --opt-code-size -lstm8 -o build/blinky.elf build/obj/stm8s_it.rel build/obj/main.rel build/obj/stm8s_adc1.rel build/obj/stm8s_awu.rel build/obj/stm8s_beep.rel build/obj/stm8s_clk.rel build/obj/stm8s_exti.rel build/obj/stm8s_flash.rel build/obj/stm8s_gpio.rel build/obj/stm8s_i2c.rel build/obj/stm8s_itc.rel build/obj/stm8s_iwdg.rel build/obj/stm8s_rst.rel build/obj/stm8s_spi.rel build/obj/stm8s_tim1.rel build/obj/stm8s_tim2.rel build/obj/stm8s_uart1.rel build/obj/stm8s_wwdg.rel
```

### Generating an ihx file from the ELF file

To flash the blinky firmware to the STM8S103, we need to convert the ELF file to an ihx file. That's where `stm8-objcopy` comes in handy. The resulting `blinky.ihx` file will be placed in the `build` directory:

```bash
stm8-objcopy --remove-section=".debug*" --remove-section=SSEG --remove-section=INITIALIZED --remove-section=DATA build/blinky.elf -O ihex build/blinky.ihx
```

### Checking the size

If you're curious about the size of the binary, you can use `stm8-size` to check the size of the `blinky.ihx` file:

```bash
$ stm8-size build/blinky.ihx
   text    data     bss     dec     hex filename
      0     507       0     507     1fb build/blinky.ihx
```

Only 507 bytes of data are used! Just to put this into perspective, without DCE the binary size would be 20998 bytes:
```bash
$ stm8-size build/blinky.ihx
   text    data     bss     dec     hex filename
      0   20998       0   20998    5206 blinky.ihx
```

That's a reduction of 20491 bytes!

### Flashing the ihx file to the STM8S103

Finally, we can flash the `blinky.ihx` file to the STM8S103 using `stm8flash`. In my case, I am using a ST-Link V2 programmer:

```bash
stm8flash -c stlinkv2 -p stm8s103f3 -w build/blinky.ihx
```

### Makefile

As already mentioned, the `Makefile` in this repository automates all these steps. You can build the project by simply running `make`. A `blinky.ihx` will be generated in the `build` directory. The `Makefile` performs a size check that displays how much space of the STM8S103's 8KB flash and RAM is used. Lastly, you can upload the firmware to the STM8S103 by running `make flash` or `make upload`.