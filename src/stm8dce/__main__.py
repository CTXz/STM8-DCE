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
from . import rel_analysis
from . import settings

from .__init__ import __version__
from .asm_parser import ASMParser
from .rel_parser import RELParser


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


def run(
    input_files,
    output_dir,
    entry_label,
    exclude_functions,
    exclude_constants,
    codeseg,
    constseg,
    verbose,
    debug_flag,
    opt_irq,
):
    """
    Perform dead code elimination on the given input files.

    This function processes the specified assembly (.asm), relocatable (.rel), and library (.lib) files to identify and remove unused functions and constants.
    The processed files are stored in the specified output directory.

    Args:
        input_files (list of str): List of input file paths (ASM, rel, and lib files).
        output_dir (str): Directory where the processed ASM files will be stored.
        entry_label (str): Entry label (default: "_main").
        exclude_functions (list of str): List of function labels to exclude from dead code elimination.
        exclude_constants (list of str): List of constant labels to exclude from dead code elimination.
        codeseg (str): Name of the code segment (default: "CODE").
        constseg (str): Name of the constant segment (default: "CONST").
        verbose (bool): Enable verbose output.
        debug_flag (bool): Enable debug output.
        opt_irq (bool): Option to remove unused IRQ handlers (Caution: Removes iret's for unused interrupts!).
    """
    settings.verbose = verbose or debug_flag
    settings.debug = debug_flag
    settings.opt_irq = opt_irq
    settings.codeseg = codeseg
    settings.constseg = constseg

    # Check if output directory exists
    if not os.path.exists(output_dir):
        raise ValueError(f"Error: Output directory does not exist: {output_dir}")

    # ==========================================
    # rel and lib Parsing
    # ==========================================

    # Gather all modules from rel and lib files
    modules = []

    for input_file in input_files:
        if input_file.endswith(".rel") or input_file.endswith(".lib"):
            relparser = RELParser(input_file)
            modules += relparser.modules

    # ==========================================
    # ASM Parsing
    # ==========================================

    # Copy all files to output directory
    for file in input_files:
        if file.endswith(".asm"):
            shutil.copy(file, output_dir)

    # Parse all asm files for globals, interrupts, functions and constants
    globals = []
    interrupts = []
    functions = []
    constants = []
    initializers = []

    for output_file in os.listdir(output_dir):
        if output_file.endswith(".asm"):
            asmparser = ASMParser(os.path.join(output_dir, output_file))
            globals += asmparser.globals
            interrupts += asmparser.interrupts
            constants += asmparser.constants
            functions += asmparser.functions
            initializers += asmparser.initializers

    # ==========================================
    # Reference Resolution
    # ==========================================

    # Resolve globals assigned to functions
    debug.pdbg()
    debug.pdbg("Resolving globals assigned to functions")
    debug.pseperator()

    for function in functions:
        function.resolve_globals(globals)

    # Resolve interrupts
    debug.pdbg()
    debug.pdbg("Resolving interrupts")
    debug.pseperator()

    for function in functions:
        function.resolve_isr(interrupts)

    # Resolve function calls
    debug.pdbg()
    debug.pdbg("Resolving function calls")
    debug.pseperator()

    for function in functions:
        function.resolve_calls(functions)

    # Resolve function pointers
    debug.pdbg()
    debug.pdbg("Resolving function pointers")
    debug.pseperator()

    for function in functions:
        function.resolve_fptrs(functions)

    # Resolve globals assigned to constants
    debug.pdbg()
    debug.pdbg("Resolving globals assigned to constants")
    debug.pseperator()

    for constant in constants:
        constant.resolve_globals(globals)

    # Resolve constants loaded by functions
    debug.pdbg()
    debug.pdbg("Resolving constants loaded by functions")
    debug.pseperator()

    for function in functions:
        function.resolve_constants(constants)

    # Resolve functions and constants accessed by initializers
    debug.pdbg()
    debug.pdbg("Resolving functions and constants accessed by initializers")
    debug.pseperator()

    for initializer in initializers:
        initializer.resolve_pointers(functions, constants)

    # ==========================================
    # Dead Code Evaluation
    # ==========================================

    keep_functions = []
    keep_constants = []

    # Get entry function object
    entry_function = asm_analysis.functions_by_name(functions, entry_label)

    if entry_function:
        if len(entry_function) > 1:
            raise ValueError(
                f"Error: Multiple definitions for entry label: {entry_label}"
            )

        entry_function = entry_function[0]

        # Keep entry function and all of its traversed functions
        debug.pdbg()
        debug.pdbg(f"Traversing entry function: {entry_label}")
        debug.pseperator()
        keep_functions += [entry_function] + asm_analysis.traverse_functions(
            functions, entry_function
        )
    elif modules:
        # If it's not provided in the asm files, try to look for it in rel and lib files
        debug.pdbg()
        debug.pdbg("Entry label not found in ASM files, looking in rel and lib files")

        entry_module = rel_analysis.modules_by_defined_symbol(modules, entry_label)
        if not entry_module:
            raise ValueError(f"Error: Entry label not found: {entry_label}")
        if len(entry_module) > 1:
            raise ValueError(
                f"Error: Multiple definitions for entry label: {entry_label}"
            )

        entry_module = entry_module[0]

        debug.pdbg(
            f"Entry label found in {entry_module.path}:{entry_module.line_number} in module {entry_module.name}"
        )

        entry_module.resolve_outgoing_references(functions, constants)
        for function in entry_module.references:
            debug.pdbg()
            debug.pdbg(
                f"Traversing function {function.name} referenced by module {entry_module.name}"
            )
            debug.pseperator()
            keep_functions += [function] + asm_analysis.traverse_functions(
                functions, function
            )
    else:
        raise ValueError(f"Error: Entry label not found: {entry_label}")

    # Keep interrupt handlers and all of their traversed functions
    # but exclude unused IRQ handlers if opted by the user
    interrupt_handlers = asm_analysis.interrupt_handlers(functions)
    for handler in interrupt_handlers:
        if settings.opt_irq and handler.empty:
            continue
        debug.pdbg()
        debug.pdbg(f"Traversing IRQ handler: {handler.name}")
        debug.pseperator()
        keep_functions += [handler] + asm_analysis.traverse_functions(
            functions, handler
        )

    # Keep functions accessed by initializers
    for initializer in initializers:
        for function_pointer in initializer.function_pointers:
            if (
                isinstance(function_pointer, asm_analysis.Function)
                and function_pointer not in keep_functions
            ):
                debug.pdbg()
                debug.pdbg(
                    f"Traversing function {function_pointer.name} accessed by initializer"
                )
                debug.pseperator()
                keep_functions += [function_pointer] + asm_analysis.traverse_functions(
                    functions, function_pointer
                )

    # Keep functions excluded by the user and all of their traversed functions
    if exclude_functions:
        for exclude_name in exclude_functions:
            filename, name = eval_flabel(exclude_name)
            if filename:
                excluded_function = asm_analysis.function_by_filename_name(
                    functions, filename, name
                )
            else:
                excluded_function = asm_analysis.functions_by_name(functions, name)
                if len(excluded_function) > 1:
                    raise ValueError(
                        f"Error: Multiple possible definitions for excluded function: {name}"
                    )

                excluded_function = excluded_function[0] if excluded_function else None

            if not excluded_function:
                print(f"Warning: Excluded function not found: {name}")
                continue

            if excluded_function not in keep_functions:
                debug.pdbg()
                debug.pdbg(f"Traversing excluded function: {name}")
                debug.pseperator()
                keep_functions += [excluded_function] + asm_analysis.traverse_functions(
                    functions, excluded_function
                )

    # Remove duplicates
    keep_functions = list(set(keep_functions))

    # Resolve external references
    for module in modules:
        module.resolve_references(keep_functions, initializers, functions, constants)

    # Keep functions and constants that are referenced by lib and rel files
    for module in modules:
        for ref in module.references:
            if isinstance(ref, asm_analysis.Function) and ref not in keep_functions:
                debug.pdbg()
                debug.pdbg(
                    f"Traversing function {ref.name} referenced by module {module.name}"
                )
                debug.pseperator()
                keep_functions += [ref] + asm_analysis.traverse_functions(
                    functions, ref
                )
            elif isinstance(ref, asm_analysis.Constant) and ref not in keep_constants:
                keep_constants.append(ref)

    # Once again, remove possible duplicates
    keep_functions = list(set(keep_functions))

    # Keep constants loaded by kept functions
    for kept_function in keep_functions:
        keep_constants += kept_function.constants

    # Keep constants accessed by initializers
    for initializer in initializers:
        for constant in initializer.constant_pointers:
            if constant not in keep_constants:
                keep_constants.append(constant)

    # Keep excluded constants
    if exclude_constants:
        for excluded_const_name in exclude_constants:
            filename, name = eval_flabel(excluded_const_name)
            if filename:
                excluded_constant = asm_analysis.constant_by_filename_name(
                    constants, filename, name
                )
            else:
                excluded_constant = asm_analysis.constants_by_name(constants, name)
                if len(excluded_constant) > 1:
                    raise ValueError(
                        f"Error: Multiple possible definitions for excluded constant: {name}"
                    )

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

    # Return removed and kept functions and constants for testing
    return remove_functions, remove_constants, keep_functions, keep_constants


def main():
    """
    The main function of the STM8DCE tool.
    Parses command-line arguments and calls the run function.
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
    parser.add_argument(
        "--codeseg", help="Code segment name (default: CODE)", type=str, default="CODE"
    )
    parser.add_argument(
        "--constseg",
        help="Constant segment name (default: CONST)",
        type=str,
        default="CONST",
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

    run(
        input_files=args.input,
        output_dir=args.output,
        entry_label=args.entry,
        exclude_functions=args.exclude_function,
        exclude_constants=args.exclude_constant,
        codeseg=args.codeseg,
        constseg=args.constseg,
        verbose=args.verbose,
        debug_flag=args.debug,
        opt_irq=args.opt_irq,
    )


if __name__ == "__main__":
    main()
