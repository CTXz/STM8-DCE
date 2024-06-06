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

import os
import argparse
import shutil
from enum import Enum

from . import parsers
from . import debug
from . import matchers
from . import analysis
from . import settings
from .__init__ import __version__

############################################
# Constants
############################################

# List of functions that SDCC may require
SDCC_REQ = [
    "_getchar", # See 3.14.2 of the SDCC manual
    "_putchar" # See 3.14.2 of the SDCC manual
]

############################################
# Arg Parsing
############################################


# Evaluate a function label for exclusion
# User can either specify function label
# as is (ex. _hello), or with its filename
# (ex. file.asm:_hello) to allow exclusion
# for cases where multiple functions have
# the same name
# Returns a tuple of filename and name
# if filename is not specified, filename is None
def eval_flabel(flabel):
    if ":" in flabel:
        filename, name = flabel.split(":")
        return filename, name
    return None, flabel


############################################
# Main
############################################


def main():
    # ==========================================
    # Arg Parsing
    # ==========================================
    parser = argparse.ArgumentParser(description="STM8 SDCC dead code elimination tool")
    parser.add_argument("input", nargs="+", help="ASM files to process", type=str)
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
    parser.add_argument
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

    parser.epilog = "Example: stm8dce file1.asm file2.asm ... -o output/"

    args = parser.parse_args()

    settings.verbose = args.verbose or args.debug
    settings.debug = args.debug
    settings.opt_irq = args.opt_irq

    # Check if output directory exists
    if not os.path.exists(args.output):
        print("Error: Output directory does not exist:", args.output)
        exit(1)

    # Copy all files to args.output directory
    for file in args.input:
        shutil.copy(file, args.output)

    # ==========================================
    # ASM Parsing
    # ==========================================

    # Parse all asm files for globals, interrupts, functions and constants
    # - globals is a list of GlobalDef objects
    # - interrupts is a list of IntDef objects
    # - functions is a list of Function objects
    # - constants is a list of Constant objects
    globals = []
    interrupts = []
    functions = []
    constants = []
    for file in os.listdir(args.output):
        if file.endswith(".asm"):
            g, i, c, f = parsers.parse_file(args.output + "/" + file)
            globals += g
            interrupts += i
            constants += c
            functions += f

    # ==========================================
    # Reference Resolution
    # ==========================================

    # Resolve globals assigned to functions
    if settings.debug:
        print()
        print("Resolving globals assigned to functions")
        debug.pseperator()

    for f in functions:
        f.resolve_globals(globals)

    # Resolve interrupts
    if settings.debug:
        print()
        print("Resolving interrupts")
        debug.pseperator()

    for f in functions:
        f.resolve_isr(interrupts)

    # Resolve function calls
    if settings.debug:
        print()
        print("Resolving function calls")
        debug.pseperator()

    for f in functions:
        f.resolve_calls(functions)

    # Resolve function pointers
    if settings.debug:
        print()
        print("Resolving function pointers")
        debug.pseperator()

    for f in functions:
        f.resolve_fptrs(functions)

    # Resolve globals assigned to constants
    if settings.debug:
        print()
        print("Resolving globals assigned to constants")
        debug.pseperator()

    for c in constants:
        c.resolve_globals(globals)

    # Resolve constants loaded by functions
    if settings.debug:
        print()
        print("Resolving constants loaded by functions")
        debug.pseperator()

    for f in functions:
        f.resolve_constants(constants)

    # ==========================================
    # Dead Code Evaluation
    # ==========================================

    # Get entry function object
    mainf = analysis.functions_by_name(functions, args.entry)
    if not mainf:
        print("Error: Entry label not found:", args.entry)
        exit(1)
    elif len(mainf) > 1:
        print("Error: Multiple definitions for entry label:", args.entry)
        for f in mainf:
            print("In file {}:{}".format(f.path, f.start_line))
        exit(1)

    mainf = mainf[0]

    # Keep main function and all of its traversed calls
    if settings.debug:
        print()
        print("Traversing entry function:", args.entry)
        debug.pseperator()
    keepf = [mainf] + analysis.traverse_calls(functions, mainf)

    # Keep functions assigned to a function pointer
    for f in functions:
        for fp in f.fptrs:
            if fp not in keepf:
                if settings.debug:
                    print()
                    print("Traversing function assigned to function pointer:", fp.name)
                    debug.pseperator()
                keepf += [fp] + analysis.traverse_calls(functions, fp)

    # Keep interrupt handlers and all of their traversed calls
    # but exclude unused IRQ handlers if opted by the user
    ihandlers = analysis.interrupt_handlers(functions)
    for ih in ihandlers:
        if settings.opt_irq and ih.empty:
            continue
        if settings.debug:
            print()
            print("Traversing IRQ handler:", ih.name)
            debug.pseperator()
        keepf += [ih] + analysis.traverse_calls(functions, ih)

    # Keep functions excluded by the user and all of their traversed calls
    if args.exclude_function:
        for name in args.exclude_function:
            filename, name = eval_flabel(name)
            if filename:
                f = analysis.function_by_filename_name(functions, filename, name)
            else:
                f = analysis.functions_by_name(functions, name)
                if len(f) > 1:
                    print(
                        "Error: Multiple possible definitions for excluded function:",
                        name,
                    )
                    for f in f:
                        print("In file {}:{}".format(f.path, f.start_line))
                    print(
                        "Please use the format file.asm:label to specify the exact function to exclude"
                    )
                    exit(1)
                f = f[0] if f else None

            if not f:
                print("Warning: Excluded function not found:", name)
                continue

            if f not in keepf:
                if settings.debug:
                    print()
                    print("Traversing excluded function:", name)
                    debug.pseperator()
                keepf += [f] + analysis.traverse_calls(functions, f)

    # Do not exclude functions that may be required by SDCC
    for name in SDCC_REQ:
        f = analysis.functions_by_name(functions, name)

        if not f:
            continue

        if len(f) > 1:
            print(
                "Error: Multiple possible definitions for SDCC required function:",
                name,
            )
            for f in f:
                print("In file {}:{}".format(f.path, f.start_line))
            exit(1)

        f = f[0]
        
        if f not in keepf:
            if settings.debug:
                print()
                print("Traversing SDCC required function:", name)
                debug.pseperator()
            keepf += [f] + analysis.traverse_calls(functions, f)

    # Remove duplicates
    keepf = list(set(keepf))

    # Keep constants loaded by kept functions
    keepc = []
    for f in keepf:
        keepc += f.constants

    # Keep excluded constants
    if args.exclude_constant:
        for name in args.exclude_constant:
            filename, name = eval_flabel(name)
            if filename:
                c = analysis.constant_by_filename_name(constants, filename, name)
            else:
                c = analysis.constants_by_name(constants, name)
                if len(c) > 1:
                    print(
                        "Error: Multiple possible definitions for excluded constant:",
                        name,
                    )
                    for c in c:
                        print("In file {}:{}".format(c.path, c.start_line))
                    print(
                        "Please use the format file.asm:label to specify the exact constant to exclude"
                    )
                    exit(1)
                c = c[0] if c else None

            if not c:
                print("Warning: Excluded constant not found:", name)
                continue

            if c and (c not in keepc):
                keepc.append(c)

    # Remove duplicates
    keepc = list(set(keepc))

    # Remove functions that are not in keepf
    removef = [f for f in functions if f not in keepf]

    # Remove global labels assigned to removed functions
    removeg = []
    for f in removef:
        removeg += f.global_defs

    # Remove interrupt definitions assigned to removed IRQ handlers
    removei = []
    for f in removef:
        if f.isr_def:
            removei.append(f.isr_def)

    # Remove constants that are not in keepc
    removec = [c for c in constants if c not in keepc]

    # Remove global labels assigned to removed constants
    removeg += [g for c in removec for g in c.global_defs]

    if settings.verbose:
        print()
        print("Removing Functions:")
        for f in removef:
            print("\t{} - {}:{}".format(f.name, f.path, f.start_line))
        print()
        print("Removing Constants:")
        for c in removec:
            print("\t{} - {}:{}".format(c.name, c.path, c.start_line))
        print()

    # ==========================================
    # Dead Code Removal
    # ==========================================

    # Group functions, globals, int defs and constants by file to reduce file I/O
    filef = {}
    fileg = {}
    filei = {}
    filec = {}
    for f in removef:
        if f.path not in filef:
            filef[f.path] = []
        filef[f.path].append(f)
    for g in removeg:
        if g.path not in fileg:
            fileg[g.path] = []
        fileg[g.path].append(g)
    for i in removei:
        if i.path not in filei:
            filei[i.path] = []
        filei[i.path].append(i)
    for c in removec:
        if c.path not in filec:
            filec[c.path] = []
        filec[c.path].append(c)

    # Remove (comment out) unused functions,
    # global definitions, interrupt definitions
    # and constants from the files
    for file in filef:
        with open(file, "r") as f:
            lines = f.readlines()

        # Global definitions
        if file in fileg:
            for g in fileg[file]:
                lines[g.line - 1] = ";" + lines[g.line - 1]
            fileg[file].remove(g)

        # Interrupt definitions
        # These must be set to 0x000000 instead of being commented out.
        # else remaining IRQ handlers will be moved to a different VTABLE
        # entry!
        if file in filei:
            for i in filei[file]:
                lines[i.line - 1] = "	int 0x000000\n"
            filei[file].remove(i)

        # Functions
        if file in filef:
            for f in filef[file]:
                for i in range(f.start_line - 1, f.end_line):
                    lines[i] = ";" + lines[i]

        # Constants
        if file in filec:
            for c in filec[file]:
                for i in range(c.start_line - 1, c.end_line):
                    lines[i] = ";" + lines[i]

        with open(file, "w") as f:
            f.writelines(lines)

    # Remove any remaing global definitions
    # assigned to removed functions
    # This catches any global labels that import unused
    # functions from other files
    for file in fileg:
        with open(file, "r") as f:
            lines = f.readlines()

        for g in fileg[file]:
            lines[g.line - 1] = ";" + lines[g.line - 1]

        with open(file, "w") as f:
            f.writelines(lines)

    # Remove interrupt definitions assigned to removed IRQ handlers
    # if they haven't already been removed
    for file in filei:
        with open(file, "r") as f:
            lines = f.readlines()

        for i in filei[file]:
            lines[i.line - 1] = "	int 0x000000\n"

        with open(file, "w") as f:
            f.writelines(lines)

    # Remove any remaining constants
    for file in filec:
        with open(file, "r") as f:
            lines = f.readlines()

        for c in filec[file]:
            for i in range(c.start_line - 1, c.end_line):
                lines[i] = ";" + lines[i]

        with open(file, "w") as f:
            f.writelines(lines)

    # ==========================================
    # Summary
    # ==========================================

    print("Detected and removed:")
    print(
        "{} unused functions from a total of {} functions".format(
            len(removef), len(functions)
        )
    )
    print(
        "{} unused constants from a total of {} constants".format(
            len(removec), len(constants)
        )
    )


if __name__ == "__main__":
    main()
