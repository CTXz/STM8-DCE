# STM8-DCE - A SDCC STM8 Dead Code Elimination Tool <!-- omit in toc -->

*Gone are the days of cherry picking the Standard Peripheral Library!*

## Table of Contents <!-- omit in toc -->
- [Features](#features)
- [Issues](#issues)
- [Disclaimer](#disclaimer)
- [Installation](#installation)
- [Usage](#usage)
  - [Examples](#examples)
    - [DCE without Interrupt Optimization](#dce-without-interrupt-optimization)
    - [Adding .rel and .lib Files](#adding-rel-and-lib-files)
    - [DCE with Interrupt Optimization](#dce-with-interrupt-optimization)
    - [Alternative Entry Label](#alternative-entry-label)
    - [Exclude Functions and Constants](#exclude-functions-and-constants)
    - [Verbose Output](#verbose-output)
    - [Debug Output](#debug-output)
- [What about XaviDCR92's sdcc-gas fork](#what-about-xavidcr92s-sdcc-gas-fork)
- [How the tool works](#how-the-tool-works)
- [Reporting Issues \& Contributing](#reporting-issues--contributing)


## Features

This tool has been largely inspired by [@XaviDCR92's sdccrm tool](https://github.com/XaviDCR92/sdccrm) and aims to provide a couple more improvements. Most imporatantly, the tool:

- Has been written for the latest version of SDCC (4.4.1 at the time of writing)
- Removes unused functions
- Removes unused constants
- Removes unused interrupt handlers (if `--opt-irq` is provided)
- Is capable of distinguishing between global and local/static labels
- Detects function pointers and keeps functions that are assigned to a function pointer

Due to [sdccrm's](https://github.com/XaviDCR92/sdccrm) deprecated status and my personal preference for Python over C for pattern matching and text processing, I chose to develop the tool completely from scratch instead of forking [sdccrm](https://github.com/XaviDCR92/sdccrm).

## Issues

This tool has **not been tested with debug information enabled**. Enabling debug information will likely optimize significantly less code and probably mess with debug symbols.

## Disclaimer

Please note that this tool is still in early development and has not been thoroughly tested yet. So far, I have only tested it on numerous of my own projects where the tool delivers the expected results. That being said, I may have overlooked certain edge cases which could in the very worst case lead to the tool removing code that should not be removed. Hence, proceed with caution!

## Installation

The tool has been written in Python 3 and is available on PyPI. You can install it using pip:

```bash
$ pip install stm8dce
```

Alternatively, you can clone the repository, and install it from the source:

```bash
$ git clone https://github.com/CTXz/STM8-DCE.git
$ cd STM8-DCE
$ pip install .
```

## Usage

```
usage: stm8dce [-h] -o OUTPUT [-e ENTRY] [-xf EXCLUDE_FUNCTION [EXCLUDE_FUNCTION ...]] [-xc EXCLUDE_CONSTANT [EXCLUDE_CONSTANT ...]] [--codeseg CODESEG] [--constseg CONSTSEG] [-v] [-d] [--version] [--opt-irq]
               input [input ...]

STM8 SDCC dead code elimination tool

positional arguments:
  input                 ASM, rel and lib files

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory to store processed ASM files
  -e ENTRY, --entry ENTRY
                        Entry label
  -xf EXCLUDE_FUNCTION [EXCLUDE_FUNCTION ...], --exclude-function EXCLUDE_FUNCTION [EXCLUDE_FUNCTION ...]
                        Exclude functions
  -xc EXCLUDE_CONSTANT [EXCLUDE_CONSTANT ...], --exclude-constant EXCLUDE_CONSTANT [EXCLUDE_CONSTANT ...]
                        Exclude interrupt handlers
  --codeseg CODESEG     Code segment name (default: CODE)
  --constseg CONSTSEG   Constant segment name (default: CONST)
  -v, --verbose         Verbose output
  -d, --debug           Debug output
  --version             show program's version number and exit
  --opt-irq             Remove unused IRQ handlers (Caution: Removes iret's for unused interrupts!)

Example: stm8dce file1.asm file2.asm file3.rel file4.lib ... -o output/
```

The tool receives a list of SDCC generated assembly-, lib- and rel files for the STM8 as input and outputs the optimized assembly files to the specified output directory.

The `.lib` and `.rel` files aren't processed, but are necessary for stm8dce to ensure that functions used by these files aren't accidentally removed (See ["Adding .rel and .lib Files"](#adding-rel-and-lib-files)). Additionally the `--opt-irq` flag may be provided to also eliminate unused interrupt handlers.

> Note: Optimizing away interrupt handlers will strip away their default behaivour of returning from the interrupt. This means, if a unused interrupt handler is accidentally triggered, the STM8 will likely crash. Use this feature with caution and ensure that only handled interrupts are enabled in your firmware!

### Examples

For a practical demonstration, check out the [example](example/) directory in this repository. It features a straightforward Test project designed for the STM8S103, complete with a Makefile and a comprehensive README that walks you through the entire process: from compiling your project into assembly files, to optimizing them with `stm8dce`, and finally assembling and linking them together into an elf and ihx file. The project also includes all STM8S103-compatible modules from the SPL to really showcase the tools capability. Without DCE, incorporating all modules would quickly surpass the STM8S103's flash memory capacity.

For a quick demonstration however, the following examples will suffice:

#### DCE without Interrupt Optimization

Suppose SDCC generated us a couple of assembly files for our STM8 project:
```bash
main.asm stm8s_it.asm stm8s_gpio.asm
```

To perform dead code elimination on these files, we can simply run:

```bash
$ mkdir output
$ stm8dce -o output main.asm stm8s_it.asm stm8s_gpio.asm
``` 

This will output the optimized assembly files to the `output` directory.

#### Adding .rel and .lib Files

When using precompiled libraries or object files in your project, these files may reference functions defined in your project's assembly files. In such cases, you should provide these `.rel` and `.lib` files to the tool. While the tool does not process these files, it ensures that functions used by them are not mistakenly removed.

For example, if your code uses the `printf` function from the standard library, you must provide the standard library to the tool. Otherwise, it might remove the `putchar` function, which is required by `printf`, leading to a linker error:

```
?ASlink-Warning-Undefined Global '_putchar' referenced by module 'puts'
```

To prevent this, include the standard library when running the tool:
```bash
mkdir output
stm8dce -o output main.asm stm8s_it.asm stm8s_gpio.asm path/to/stm8.lib
```

Typically, the standard library is located in the `lib` directory of your SDCC installation. On Linux systems, this is usually found at `/usr/share/sdcc/lib/stm8/stm8.lib` or `/usr/local/share/sdcc/lib/stm8/stm8.lib`.

Similarly, you can provide `.rel` files to the tool:
```bash
stm8dce -o output main.asm stm8s_it.asm some.rel some_other.rel
```

#### DCE with Interrupt Optimization

Lets assume we want to optimize the same files as before, but also eliminate unused interrupt handlers:

```bash
$ mkdir output
$ stm8dce --opt-irq -o output main.asm stm8s_it.asm stm8s_gpio.asm
```
This should result in a slightly reduced code size (unless all interrupts are utilized, which is highly improbable), as unused interrupt handlers are eliminated.
However, this optimization comes with a minor "drawback": the tool removes the default `iret` instruction from unused interrupt handlers. Consequently, if an unused interrupt handler is accidentally triggered, the STM8 may crash. Use this feature with caution and ensure that only handled interrupts are enabled in your firmware!

#### Alternative Entry Label

By default, the tool will assume that the entry label is `_main`. If your entry label is different, you can specify it with the `-e` flag:

```bash
$ stm8dce -e _my_entry_label -o output main.asm stm8s_it.asm stm8s_gpio.asm
```

#### Exclude Functions and Constants

If you want to exclude certain functions or constants from being optimized away, you can do so by providing the `-xf <function>` or `-xc <constant>` flags. Note that these must be provided as they are named in the assembly files (i.e. they contain a leading underscore: `hello_world` -> `_hello_world`). This may be useful if you want to keep certain functions or constants for debugging purposes, or if the tool does end up removing code that should not be removed. If the latter is the case, please don't hesitate to open an issue on this repository!

```bash
$ stm8dce -xf _my_debug_function1 _my_debug_function2 -xc _MY_DEBUG_CONSTANT1 _MY_DEBUG_CONSTANT2 -o output main.asm stm8s_it.asm stm8s_gpio.asm
```

In certain cases, there may be multiple local/static functions or constants with the same name in different files. If that is the case, the previous example will generate an error. In this case, you can specify the file name of the function or constant label as well:

```bash
$ stm8dce -xf main.asm:_my_debug_function -xc main.asm:_MY_DEBUG_CONSTANT -o output main.asm stm8s_it.asm stm8s_gpio.asm
```

#### Verbose Output

If you want to see which functions and constants have been optimized away, you can provide the `-v` flag:

```bash
$ stm8dce -v -o output main.asm stm8s_it.asm stm8s_gpio.asm

Removing Functions:
	_unused_function - main.asm:123
	_another_unused_function - main.asm:456
	...

Removing Constants:
	_UNUSED_CONSTANT - main.asm:3
	_ANOTHER_UNUSED_CONSTANT - main.asm:4
	...
```

#### Debug Output

Debug output can be activated using the `-d` flag, offering verbose output and showcasing the tool's intermediate steps. Note that the output will quickly flood your terminal and is best redirected to a log file instead. Debug output primarily serves developers who wish to contribute to the project. It can also be useful for resolving issues with the tool.

```bash
$ stm8dce -d -o output main.asm stm8s_it.asm stm8s_gpio.asm > debug.log
```

## What about XaviDCR92's sdcc-gas fork

@XaviDCR92's [sdccrm](https://github.com/XaviDCR92/sdccrm) tool, which this project took inspiration from, has been deprecated in favor of using their [GNU Assembly-compatible SDCC fork](https://github.com/XaviDCR92/sdcc-gas) for the STM8 along with their [stm8-binutils](https://github.com/XaviDCR92/stm8-binutils-gdb) fork to perform linking-time dead code elimination. I found that approach to sound good in theory, but in practice, the implementation comes with numerous issues, such as being incompatible with newer versions of SDCC, and the fact that SDCC's standard library has to be compiled manually if one requires it. [Even once the standard library has been compiled, it uses platform-independent C code, which is not as optimized as the platform- specific assembly functions tailored for the STM8](https://github.com/XaviDCR92/stm8-dce-example/issues/2). I believe all of this mostly boils down to the fact that the SDCC fork's changes are not eligible for merging into the main SDCC repository, making it difficult to maintain and somewhat akward to use.

## How the tool works

This section is still work in progress but will hopefully provide a brief overview of how the tool works.
For the time being, take a peek at the source code. I've tried my best to add sufficient comments!

## Reporting Issues & Contributing

If you encounter any issues with the tool, please don't hesitate to open an issue on this repository. If you have any suggestions or feature requests, feel free to open an issue as well!

If you want to contribute to the project, feel free to fork the repository and open a pull request. I'm happy to review any contributions!
