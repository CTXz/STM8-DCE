# Copyright (C) 2024 Patrick Pedersen

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# SDCC STM8 Dead Code Elimination Tool
# Description: Main file for the STM8 SDCC dead code elimination tool.

# Credits: This tool has been largely inspired by XaviDCR92's sdccrm tool:
#          https://github.com/XaviDCR92/sdccrm
#

"""
SDCC STM8 Dead Code Elimination Tool
"""

import os
import argparse
import shutil

from . import debug
from . import asm_analysis
from . import settings

from .__init__ import __version__
from .asm_parser import ASMParser
from .rel_parser import RELParser

############################################
# Arg Parsing
############################################


def eval_flabel(flabel):
    """
    Evaluates a function label for exclusion.

    Users can specify a function label either as is (e.g., _hello) or with its filename (e.g., file.asm:_hello)
    to allow exclusion for cases where multiple functions have the same name.

    Args:
        flabel (str): The function label to evaluate.

    Returns:
        tuple: A tuple of filename and name. If the filename is not specified, filename is None.
    """
    if ":" in flabel:
        filename, name = flabel.split(":")
        return filename, name
    return None, flabel


############################################
# Main
############################################


def main():
    """
    The main function of the STM8DCE tool.
    Parses command-line arguments, processes the specified assembly files, and performs dead code elimination.
    """
    # ==========================================
    # Arg Parsing
    # ==========================================
    parser = argparse.ArgumentParser(description="STM8 SDCC dead code elimination tool")
    parser.add_argument("input", nargs="+", help="ASM, rel and lib files", type=str)
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory to store processed ASM files",
        required=True,
    )
    parser.add_argument("-e", "--entry", help="Entry label", type=str, default="_main")
    parser.add_argument(
        "-xf", "--exclude-function", help="Exclude functions", type=str, nargs="+"
    )
    parser.add_argument(
        "-xc",
        "--exclude-constant",
        help="Exclude interrupt handlers",
        type=str,
        nargs="+",
    )
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    parser.add_argument("-d", "--debug", help="Debug output", action="store_true")
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )
    parser.add_argument(
        "--opt-irq",
        help="Remove unused IRQ handlers (Caution: Removes iret's for unused interrupts!)",
        action="store_true",
    )

    parser.epilog = (
        "Example: stm8dce file1.asm file2.asm file3.rel file4.lib ... -o output/"
    )

    args = parser.parse_args()

    settings.verbose = args.verbose or args.debug
    settings.debug = args.debug
    settings.opt_irq = args.opt_irq

    # Check if output directory exists
    if not os.path.exists(args.output):
        print(f"Error: Output directory does not exist: {args.output}")
        exit(1)

    # ==========================================
    # rel and lib Parsing
    # ==========================================

    # Gather all modules from rel and lib files
    modules = []

    for input_file in args.input:
        if input_file.endswith(".rel") or input_file.endswith(".lib"):
            relparser = RELParser(input_file)
            modules += relparser.modules

    # ==========================================
    # ASM Parsing
    # ==========================================

    # Copy all files to args.output directory
    for asm_file in args.input:
        shutil.copy(asm_file, args.output)

    # Parse all asm files for globals, interrupts, functions and constants
    # - globals is a list of GlobalDef objects
    # - interrupts is a list of IntDef objects
    # - functions is a list of Function objects
    # - constants is a list of Constant objects
    globals = []
    interrupts = []
    functions = []
    constants = []

    for output_file in os.listdir(args.output):
        if output_file.endswith(".asm"):
            # g_defs, i_defs, c_defs, f_defs = asm_parsers.parse_file(
            #     args.output + "/" + output_file
            # )
            asmparser = ASMParser(args.output + "/" + output_file)

            globals += asmparser.globals
            interrupts += asmparser.interrupts
            constants += asmparser.constants
            functions += asmparser.functions

    # ==========================================
    # Reference Resolution
    # ==========================================

    # Resolve globals assigned to functions
    if settings.debug:
        print()
        print("Resolving globals assigned to functions")
        debug.pseperator()

    for function in functions:
        function.resolve_globals(globals)

    # Resolve interrupts
    if settings.debug:
        print()
        print("Resolving interrupts")
        debug.pseperator()

    for function in functions:
        function.resolve_isr(interrupts)

    # Resolve function calls
    if settings.debug:
        print()
        print("Resolving function calls")
        debug.pseperator()

    for function in functions:
        function.resolve_calls(functions)

    # Resolve function pointers
    if settings.debug:
        print()
        print("Resolving function pointers")
        debug.pseperator()

    for function in functions:
        function.resolve_fptrs(functions)

    # Resolve globals assigned to constants
    if settings.debug:
        print()
        print("Resolving globals assigned to constants")
        debug.pseperator()

    for constant in constants:
        constant.resolve_globals(globals)

    # Resolve constants loaded by functions
    if settings.debug:
        print()
        print("Resolving constants loaded by functions")
        debug.pseperator()

    for function in functions:
        function.resolve_constants(constants)

    # Resolve external references
    for module in modules:
        module.resolve_references(functions, constants)

    # ==========================================
    # Dead Code Evaluation
    # ==========================================

    # Get entry function object
    entry_function = asm_analysis.functions_by_name(functions, args.entry)
    if not entry_function:
        print(f"Error: Entry label not found: {args.entry}")
        exit(1)
    elif len(entry_function) > 1:
        print(f"Error: Multiple definitions for entry label: {args.entry}")
        for entry_func in entry_function:
            print(f"In file {entry_func.path}:{entry_func.start_line_number}")
        exit(1)

    entry_function = entry_function[0]

    # Keep main function and all of its traversed calls
    if settings.debug:
        print()
        print(f"Traversing entry function: {args.entry}")
        debug.pseperator()
    keep_functions = [entry_function] + asm_analysis.traverse_calls(
        functions, entry_function
    )

    # Keep functions assigned to a function pointer
    for func in functions:
        for func_pointer in func.fptrs:
            if func_pointer not in keep_functions:
                if settings.debug:
                    print()
                    print(
                        f"Traversing function assigned to function pointer: {func_pointer.name}"
                    )
                    debug.pseperator()
                keep_functions += [func_pointer] + asm_analysis.traverse_calls(
                    functions, func_pointer
                )

    # Keep interrupt handlers and all of their traversed calls
    # but exclude unused IRQ handlers if opted by the user
    interrupt_handlers = asm_analysis.interrupt_handlers(functions)
    for handler in interrupt_handlers:
        if settings.opt_irq and handler.empty:
            continue
        if settings.debug:
            print()
            print(f"Traversing IRQ handler: {handler.name}")
            debug.pseperator()
        keep_functions += [handler] + asm_analysis.traverse_calls(functions, handler)

    # Keep functions excluded by the user and all of their traversed calls
    if args.exclude_function:
        for exclude_name in args.exclude_function:
            filename, name = eval_flabel(exclude_name)
            if filename:
                excluded_function = asm_analysis.function_by_filename_name(
                    functions, filename, name
                )
            else:
                excluded_function = asm_analysis.functions_by_name(functions, name)
                if len(excluded_function) > 1:
                    print(
                        f"Error: Multiple possible definitions for excluded function: {name}"
                    )
                    for ex_func in excluded_function:
                        print(f"In file {ex_func.path}:{ex_func.start_line_number}")
                    print(
                        "Please use the format file.asm:label to specify the exact function to exclude"
                    )
                    exit(1)
                excluded_function = excluded_function[0] if excluded_function else None

            if not excluded_function:
                print(f"Warning: Excluded function not found: {name}")
                continue

            if excluded_function not in keep_functions:
                if settings.debug:
                    print()
                    print(f"Traversing excluded function: {name}")
                    debug.pseperator()
                keep_functions += [excluded_function] + asm_analysis.traverse_calls(
                    functions, excluded_function
                )

    # Keep functions that are referenced by lib and rel files
    for module in modules:
        for function in module.references:
            if function not in keep_functions:
                if settings.debug:
                    print()
                    print(
                        f"Traversing function {function.name} referenced by module {module.name}"
                    )
                    debug.pseperator()
                keep_functions += [function] + asm_analysis.traverse_calls(
                    functions, function
                )

    # Remove duplicates
    keep_functions = list(set(keep_functions))

    # Keep constants loaded by kept functions
    keep_constants = []
    for kept_function in keep_functions:
        keep_constants += kept_function.constants

    # Keep excluded constants
    if args.exclude_constant:
        for excluded_const_name in args.exclude_constant:
            filename, name = eval_flabel(excluded_const_name)
            if filename:
                excluded_constant = asm_analysis.constant_by_filename_name(
                    constants, filename, name
                )
            else:
                excluded_constant = asm_analysis.constants_by_name(constants, name)
                if len(excluded_constant) > 1:
                    print(
                        f"Error: Multiple possible definitions for excluded constant: {name}"
                    )
                    for exc_const in excluded_constant:
                        print(f"In file {exc_const.path}:{exc_const.start_line_number}")
                    print(
                        "Please use the format file.asm:label to specify the exact constant to exclude"
                    )
                    exit(1)
                excluded_constant = excluded_constant[0] if excluded_constant else None

            if not excluded_constant:
                print(f"Warning: Excluded constant not found: {name}")
                continue

            if excluded_constant and (excluded_constant not in keep_constants):
                keep_constants.append(excluded_constant)

    # Remove duplicates
    keep_constants = list(set(keep_constants))

    # Remove functions that are not in keep_functions
    remove_functions = [func for func in functions if func not in keep_functions]

    # Remove global labels assigned to removed functions
    remove_globals = []
    for removed_function in remove_functions:
        remove_globals += removed_function.global_defs

    # Remove interrupt definitions assigned to removed IRQ handlers
    remove_interrupts = []
    for removed_function in remove_functions:
        if removed_function.isr_def:
            remove_interrupts.append(removed_function.isr_def)

    # Remove constants that are not in keep_constants
    remove_constants = [const for const in constants if const not in keep_constants]

    # Remove global labels assigned to removed constants
    remove_globals += [
        glob_def for const in remove_constants for glob_def in const.global_defs
    ]

    if settings.verbose:
        print()
        print("Removing Functions:")
        for removed_function in remove_functions:
            print(
                f"\t{removed_function.name} - {removed_function.path}:{removed_function.start_line_number}"
            )
        print()
        print("Removing Constants:")
        for removed_constant in remove_constants:
            print(
                f"\t{removed_constant.name} - {removed_constant.path}:{removed_constant.start_line_number}"
            )
        print()

    # ==========================================
    # Dead Code Removal
    # ==========================================

    # Group functions, globals, int defs and constants by file to reduce file I/O
    file_functions = {}
    file_globals = {}
    file_interrupts = {}
    file_constants = {}
    for removed_function in remove_functions:
        if removed_function.path not in file_functions:
            file_functions[removed_function.path] = []
        file_functions[removed_function.path].append(removed_function)
    for removed_global in remove_globals:
        if removed_global.path not in file_globals:
            file_globals[removed_global.path] = []
        file_globals[removed_global.path].append(removed_global)
    for removed_interrupt in remove_interrupts:
        if removed_interrupt.path not in file_interrupts:
            file_interrupts[removed_interrupt.path] = []
        file_interrupts[removed_interrupt.path].append(removed_interrupt)
    for removed_constant in remove_constants:
        if removed_constant.path not in file_constants:
            file_constants[removed_constant.path] = []
        file_constants[removed_constant.path].append(removed_constant)

    # Remove (comment out) unused functions,
    # global definitions, interrupt definitions
    # and constants from the files
    for file_path in file_functions:
        with open(file_path, "r") as file:
            lines = file.readlines()

        # Global definitions
        if file_path in file_globals:
            for global_def in file_globals[file_path]:
                lines[global_def.line_number - 1] = (
                    ";" + lines[global_def.line_number - 1]
                )
            file_globals[file_path].remove(global_def)

        # Interrupt definitions
        # These must be set to 0x000000 instead of being commented out.
        # else remaining IRQ handlers will be moved to a different VTABLE
        # entry!
        if file_path in file_interrupts:
            for interrupt_def in file_interrupts[file_path]:
                lines[interrupt_def.line_number - 1] = "    int 0x000000\n"
            file_interrupts[file_path].remove(interrupt_def)

        # Functions
        if file_path in file_functions:
            for function_def in file_functions[file_path]:
                for line_number in range(
                    function_def.start_line_number - 1, function_def.end_line_number
                ):
                    lines[line_number] = ";" + lines[line_number]

        # Constants
        if file_path in file_constants:
            for constant_def in file_constants[file_path]:
                for line_number in range(
                    constant_def.start_line_number - 1, constant_def.end_line_number
                ):
                    lines[line_number] = ";" + lines[line_number]

        with open(file_path, "w") as file:
            file.writelines(lines)

    # Remove any remaining global definitions
    # assigned to removed functions
    # This catches any global labels that import unused
    # functions from other files
    for file_path in file_globals:
        with open(file_path, "r") as file:
            lines = file.readlines()

        for global_def in file_globals[file_path]:
            lines[global_def.line_number - 1] = ";" + lines[global_def.line_number - 1]

        with open(file_path, "w") as file:
            file.writelines(lines)

    # Remove interrupt definitions assigned to removed IRQ handlers
    # if they haven't already been removed
    for file_path in file_interrupts:
        with open(file_path, "r") as file:
            lines = file.readlines()

        for interrupt_def in file_interrupts[file_path]:
            lines[interrupt_def.line_number - 1] = "    int 0x000000\n"

        with open(file_path, "w") as file:
            file.writelines(lines)

    # Remove any remaining constants
    for file_path in file_constants:
        with open(file_path, "r") as file:
            lines = file.readlines()

        for constant_def in file_constants[file_path]:
            for line_number in range(
                constant_def.start_line_number - 1, constant_def.end_line_number
            ):
                lines[line_number] = ";" + lines[line_number]

        with open(file_path, "w") as file:
            file.writelines(lines)

    # ==========================================
    # Summary
    # ==========================================

    print("Detected and removed:")
    print(
        f"{len(remove_functions)} unused functions from a total of {len(functions)} functions"
    )
    print(
        f"{len(remove_constants)} unused constants from a total of {len(constants)} constants"
    )


if __name__ == "__main__":
    main()
