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

"""
This module provides classes and functions helpful for analyzing SDCC generated
STM8 assembly code.
"""

from . import settings

############################################
# Classes
############################################


class GlobalDef:
    """
    Class to store global definitions.

    Attributes:
        path (str): Path of the file the global is defined in.
        name (str): Name of the global.
        line (int): Line number of the global definition.
    """

    def __init__(self, path, name, line):
        self.path = path
        self.name = name
        self.line = line

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def print(self):
        """Prints the details of the global definition."""
        print(f"Global: {self.name}")
        print(f"File: {self.path}")
        print(f"Line: {self.line}")


class IntDef:
    """
    Class to store interrupt definitions.
    Equivalent to GlobalDef, but prints differently.

    Attributes:
        path (str): Path of the file the interrupt is defined in.
        name (str): Name of the interrupt.
        line (int): Line number of the interrupt definition.
    """

    def __init__(self, path, name, line):
        self.path = path
        self.name = name
        self.line = line

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def print(self):
        """Prints the details of the interrupt definition."""
        print(f"Interrupt: {self.name}")
        print(f"File: {self.path}")
        print(f"Line: {self.line}")


class Function:
    """
    Class to store function definitions.

    Input Attributes:
        path (str): Path of the file the function is defined in.
        name (str): Name of the function.
        start_line (int): Start line of the function.
        end_line (int): End line of the function.
        calls_str (list): List of calls made by the function.
        long_read_labels_str (list): List of long read labels.

    Generated Attributes:
        calls (list): List of resolved functions called by the function (See resolve_calls).
        constants (list): List of resolved constants read by the function (See resolve_constants).
        global_defs (list): List of resolved global definitions used by the function (See resolve_globals).
        fptrs (list): List of resolved function pointers assigned by the function (See resolve_fptrs).
        isr_def (IntDef): Resolved interrupt definition associated with the function (See resolve_isr).
        empty (bool): Indicates if the function is empty.

    The intended use of this class is to first parse the input attributes and then call the resolve_* functions
    to resolve the generated attributes.
    """

    def __init__(self, path, name, start_line):
        self.path = path
        self.name = name
        self.start_line = start_line
        self.end_line = None
        self.calls_str = []
        self.long_read_labels_str = []

        self.calls = []
        self.constants = []
        self.global_defs = []
        self.fptrs = []
        self.isr_def = None
        self.empty = True

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def print(self):
        """Prints the details of the function."""
        print(f"Function: {self.name}")
        print(f"File: {self.path}")
        print(f"Start line: {self.start_line}")
        print(f"End line: {self.end_line}")
        print(f"Calls: {self.calls_str}")
        print(f"Long read labels: {self.long_read_labels_str}")
        print(f"Resolved calls: {[call.name for call in self.calls]}")
        print(f"Resolved constants: {[const.name for const in self.constants]}")
        print(
            f"Resolved global definitions: {[glob.name for glob in self.global_defs]}"
        )
        print(f"Resolved function pointers: {[fptr.name for fptr in self.fptrs]}")
        print(f"IRQ Handler: {self.isr_def}")
        print(f"Empty: {self.empty}")

    def resolve_globals(self, globals):
        """
        Resolves global definitions for the function.

        Args:
            globals (list): List of all GlobalDef objects.
        """
        for global_def in globals:
            if global_def.name == self.name:
                self.global_defs.append(global_def)
                if settings.debug:
                    print(
                        f"Global in {global_def.path}:{global_def.line} matched to function {self.name} in {self.path}:{self.start_line}"
                    )

    def resolve_isr(self, interrupts):
        """
        Resolves interrupt definitions for the function.

        Args:
            interrupts (list): List of all IntDef objects.
        """
        for interrupt in interrupts:
            if interrupt.name == self.name:
                self.isr_def = interrupt
                if settings.debug:
                    print(
                        f"Interrupt {interrupt.path}:{interrupt.line} matched to function {self.name} in {self.path}:{self.start_line}"
                    )

    def resolve_calls(self, functions):
        """
        Resolves function calls for the function.

        Precondition: Globals of all functions have been resolved first.

        Args:
            functions (list): List of all Function objects.
        """
        for call_str in self.calls_str:
            funcs = functions_by_name(functions, call_str)

            glob = any(f.global_defs for f in funcs)

            if glob:
                if len(funcs) > 1:
                    print(
                        f"Error: Conflicting definitions for non-static function: {call_str}"
                    )
                    for func in funcs:
                        print(f"In file {func.path}:{func.start_line}")
                    exit(1)
                self.calls.append(funcs[0])
                if settings.debug:
                    print(
                        f"Function {self.name} in {self.path}:{self.start_line} calls function {funcs[0].name} in {funcs[0].path}:{funcs[0].start_line}"
                    )
            else:
                matched = False
                for func in funcs:
                    if func.path == self.path:
                        if matched:
                            print(
                                f"Error: Multiple static definitions for function {func} in {func.path}"
                            )
                            exit(1)
                        self.calls.append(func)
                        if settings.debug:
                            print(
                                f"Function {self.name} in {self.path}:{self.start_line} calls static function {func.name} in {func.path}:{func.start_line}"
                            )

    def resolve_fptrs(self, functions):
        """
        Resolves function pointers assigned by the function.

        Args:
            functions (list): List of all Function objects.
        """
        for long_read_label in self.long_read_labels_str:
            for func in functions:
                if func.name == long_read_label:
                    self.fptrs.append(func)
                    if settings.debug:
                        print(
                            f"Function {self.name} in {self.path}:{self.start_line} assigns function pointer to {func.name} in {func.path}:{func.start_line}"
                        )

    def resolve_constants(self, constants):
        """
        Resolves constants for the function.

        Args:
            constants (list): List of all Constant objects.
        """
        for long_read_label in self.long_read_labels_str:
            consts = constants_by_name(constants, long_read_label)

            glob = any(const.global_defs for const in consts)

            if glob:
                if len(consts) > 1:
                    print(
                        f"Error: Conflicting definitions for global constant: {long_read_label}"
                    )
                    for const in consts:
                        print(f"In file {const.path}:{const.start_line}")
                    exit(1)
                self.constants.append(consts[0])
                if settings.debug:
                    print(
                        f"Function {self.name} in {self.path}:{self.start_line} reads global constant {long_read_label} in {consts[0].path}:{consts[0].start_line}"
                    )
            else:
                for const in consts:
                    if const.path == self.path:
                        self.constants.append(const)
                        if settings.debug:
                            print(
                                f"Function {self.name} in {self.path}:{self.start_line} reads local constant {long_read_label} in {consts[0].path}:{consts[0].start_line}"
                            )


class Constant:
    """
    Class to store constant definitions.

    Input Attributes:
        path (str): Path of the file the constant is defined in.
        name (str): Name of the constant.
        start_line (int): Start line of the constant.
        end_line (int): End line of the constant.

    Generated Attributes:
        global_defs (list): List of resolved global definitions associated with the constant (See resolve_globals).

    The intended use of this class is to first parse the input attributes and then call the resolve_* functions
    """

    def __init__(self, path, name, start_line):
        self.path = path
        self.name = name
        self.start_line = start_line
        self.end_line = None
        self.global_defs = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def print(self):
        """Prints the details of the constant."""
        print(f"Constant: {self.name}")
        print(f"File: {self.path}")
        print(f"Start line: {self.start_line}")
        print(f"End line: {self.end_line}")
        print(
            f"Resolved global definitions: {[glob.name for glob in self.global_defs]}"
        )

    def resolve_globals(self, globals):
        """
        Resolves global definitions for the constant.

        Args:
            globals (list): List of all GlobalDef objects.
        """
        for global_def in globals:
            if global_def.name == self.name:
                self.global_defs.append(global_def)
                if settings.debug:
                    print(
                        f"Global in {global_def.path}:{global_def.line} matched to constant {self.name} in {self.path}:{self.start_line}"
                    )


############################################
# Filtering & Search functions
############################################


def functions_by_name(functions, name):
    """
    Returns a list of function objects with the specified name.

    Args:
        functions (list): List of Function objects.
        name (str): Name of the function to match.

    Returns:
        list: List of matching Function objects.
    """
    return [function for function in functions if function.name == name]


def function_by_filename_name(functions, filename, name):
    """
    Returns a function object matching by filename and name from a list of functions.

    Args:
        functions (list): List of Function objects.
        filename (str): Filename to match.
        name (str): Name of the function to match.

    Returns:
        Function: Matching Function object.

    Raises:
        SystemExit: If multiple definitions for the function are found.
    """
    ret = None
    for function in functions:
        f_filename = function.path.split("/")[-1]
        if f_filename == filename and function.name == name:
            if ret:
                print(f"Error: Multiple definitions for function: {name}")
                print(f"In file {function.path}:{function.start_line}")
                exit(1)
            ret = function
    return ret


def constants_by_name(constants, name):
    """
    Returns a list of constant objects with the specified name.

    Args:
        constants (list): List of Constant objects.
        name (str): Name of the constant to match.

    Returns:
        list: List of matching Constant objects.
    """
    return [constant for constant in constants if constant.name == name]


def constant_by_filename_name(constants, filename, name):
    """
    Returns a constant object matching by filename and name from a list of constants.

    Args:
        constants (list): List of Constant objects.
        filename (str): Filename to match.
        name (str): Name of the constant to match.

    Returns:
        Constant: Matching Constant object.

    Raises:
        SystemExit: If multiple definitions for the constant are found.
    """
    ret = None
    for constant in constants:
        c_filename = constant.path.split("/")[-1]
        if c_filename == filename and constant.name == name:
            if ret:
                print(f"Error: Multiple definitions for constant: {name}")
                print(f"In file {constant.path}:{constant.start_line}")
                exit(1)
            ret = constant
    return ret


def traverse_calls(functions, top):
    """
    Traverse all calls made by a function and return a list of all traversed functions.

    Args:
        functions (list): List of Function objects.
        top (Function): The top function to start traversal from.

    Returns:
        list: List of all traversed Function objects.
    """
    if settings.debug:
        print(f"Traversing in {top.name} in {top.path}:{top.start_line}")

    ret = []

    for call in top.calls:
        if call == top:
            continue

        ret += [call] + traverse_calls(functions, call)

    if settings.debug:
        print(f"Traversing out {top.name} in {top.path}:{top.start_line}")

    return ret


def interrupt_handlers(functions):
    """
    Returns a list of all interrupt handlers in the list of functions.

    Args:
        functions (list): List of Function objects.

    Returns:
        list: List of interrupt handler Function objects.
    """
    return [function for function in functions if function.isr_def]
