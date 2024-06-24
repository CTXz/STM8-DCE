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
from . import debug

############################################
# Classes
############################################


class GlobalDef:
    """
    Class to store global definitions.

    Attributes:
        path (str): Path of the file the global is defined in.
        name (str): Name of the global.
        line_number (int): Line number of the global definition.
    """

    def __init__(self, path, line_number, name):
        self.path = path
        self.line_number = line_number
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def print(self):
        """Prints the details of the global definition."""
        print(f"Global: {self.name}")
        print(f"File: {self.path}")
        print(f"Line: {self.line_number}")


class IntDef:
    """
    Class to store interrupt definitions.
    Equivalent to GlobalDef, but prints differently.

    Attributes:
        path (str): Path of the file the interrupt is defined in.
        name (str): Name of the interrupt.
        line_number (int): Line number of the interrupt definition.
    """

    def __init__(self, path, line_number, name):
        self.path = path
        self.line_number = line_number
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def print(self):
        """Prints the details of the interrupt definition."""
        print(f"Interrupt: {self.name}")
        print(f"File: {self.path}")
        print(f"Line: {self.line_number}")


class Function:
    """
    Class to store function definitions.

    Input Attributes:
        path (str): Path of the file the function is defined in.
        start_line_number (int): Start line of the function.
        name (str): Name of the function.
        end_line_number (int): End line of the function.
        calls_str (list): List of calls made by the function.
        long_read_labels_str (list): List of long read labels.

    Generated Attributes:
        function_references (list): List of functions referenced by the function (See resolve_calls & resolve_fptrs).
        external_calls (list): List of external functions (in rel & lib files) called by the function.
        constants (list): List of resolved constants read by the function (See resolve_constants).
        external_constants (list): List of external constants (in rel & lib files) read by the function.
        global_defs (list): List of resolved global definitions used by the function (See resolve_globals).
        isr_def (IntDef): Resolved interrupt definition associated with the function (See resolve_isr).
        empty (bool): Indicates if the function is empty.

    The intended use of this class is to first parse the input attributes and then call the resolve_* functions
    to resolve the generated attributes.
    """

    def __init__(self, path, start_line_number, name):
        self.path = path
        self.start_line_number = start_line_number
        self.name = name
        self.end_line_number = None
        self.calls_str = []
        self.long_read_labels_str = []

        self.function_references = []
        self.external_calls = []
        self.constants = []
        self.external_constants = []
        self.global_defs = []
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
        print(f"Start line: {self.start_line_number}")
        print(f"End line: {self.end_line_number}")
        print(f"Calls: {self.calls_str}")
        print(f"Long read labels: {self.long_read_labels_str}")
        print(
            f"Resolved function references: {[call.name for call in self.function_references]}"
        )
        print(f"External calls: {self.external_calls}")
        print(f"Resolved constants: {[const.name for const in self.constants]}")
        print(f"External constants: {self.external_constants}")
        print(
            f"Resolved global definitions: {[glob.name for glob in self.global_defs]}"
        )
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
                debug.pdbg(
                    f"Global in {global_def.path}:{global_def.line_number} matched to function {self.name} in {self.path}:{self.start_line_number}"
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
                debug.pdbg(
                    f"Interrupt {interrupt.path}:{interrupt.line_number} matched to function {self.name} in {self.path}:{self.start_line_number}"
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

            # Probably call to external function (ex. in rel or lib)
            if not funcs:
                self.external_calls.append(call_str)
                debug.pdbg(
                    f"Function {self.name} in {self.path}:{self.start_line_number} calls external function {call_str}"
                )
                continue

            glob = any(f.global_defs for f in funcs)

            if glob:
                if len(funcs) > 1:
                    print(
                        f"Error: Conflicting definitions for non-static function: {call_str}"
                    )
                    for func in funcs:
                        print(f"In file {func.path}:{func.start_line_number}")
                    exit(1)
                self.function_references.append(funcs[0])
                debug.pdbg(
                    f"Function {self.name} in {self.path}:{self.start_line_number} calls function {funcs[0].name} in {funcs[0].path}:{funcs[0].start_line_number}"
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
                        self.function_references.append(func)
                        debug.pdbg(
                            f"Function {self.name} in {self.path}:{self.start_line_number} calls static function {func.name} in {func.path}:{func.start_line_number}"
                        )
                        matched = True

    def resolve_fptrs(self, functions):
        """
        Resolves function pointers assigned by the function.

        Args:
            functions (list): List of all Function objects.
        """
        for long_read_label in self.long_read_labels_str:
            for func in functions:
                if func.name == long_read_label:
                    self.function_references.append(func)
                    debug.pdbg(
                        f"Function {self.name} in {self.path}:{self.start_line_number} assigns function pointer to {func.name} in {func.path}:{func.start_line_number}"
                    )

    def resolve_constants(self, constants):
        """
        Resolves constants for the function.

        Args:
            constants (list): List of all Constant objects.
        """
        for long_read_label in self.long_read_labels_str:
            consts = constants_by_name(constants, long_read_label)

            if not consts:
                self.external_constants.append(long_read_label)
                debug.pdbg(
                    f"Function {self.name} in {self.path}:{self.start_line_number} reads external constant {long_read_label}"
                )
                continue

            glob = any(const.global_defs for const in consts)

            if glob:
                if len(consts) > 1:
                    print(
                        f"Error: Conflicting definitions for global constant: {long_read_label}"
                    )
                    for const in consts:
                        print(f"In file {const.path}:{const.start_line_number}")
                    exit(1)
                self.constants.append(consts[0])
                debug.pdbg(
                    f"Function {self.name} in {self.path}:{self.start_line_number} reads global constant {long_read_label} in {consts[0].path}:{consts[0].start_line_number}"
                )
            else:
                for const in consts:
                    if const.path == self.path:
                        self.constants.append(const)
                        debug.pdbg(
                            f"Function {self.name} in {self.path}:{self.start_line_number} reads local constant {long_read_label} in {consts[0].path}:{consts[0].start_line_number}"
                        )


class Constant:
    """
    Class to store constant definitions.

    Input Attributes:
        path (str): Path of the file the constant is defined in.
        start_line_number (int): Start line of the constant.
        name (str): Name of the constant.
        end_line_number (int): End line of the constant.

    Generated Attributes:
        global_defs (list): List of resolved global definitions associated with the constant (See resolve_globals).

    The intended use of this class is to first parse the input attributes and then call the resolve_* functions
    """

    def __init__(self, path, start_line_number, name):
        self.path = path
        self.start_line_number = start_line_number
        self.name = name
        self.end_line_number = None
        self.global_defs = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def print(self):
        """Prints the details of the constant."""
        print(f"Constant: {self.name}")
        print(f"File: {self.path}")
        print(f"Start line: {self.start_line_number}")
        print(f"End line: {self.end_line_number}")
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
                debug.pdbg(
                    f"Global in {global_def.path}:{global_def.line_number} matched to constant {self.name} in {self.path}:{self.start_line_number}"
                )


class Initializer:
    """
    Class to store initializer definitions.

    Input Attributes:
        path (str): Path of the file the initializer is defined in.
        start_line_number (int): Start line of the initializer.
        name (str): Name of the initializer.
        end_line_number (int): End line of the initializer.
        pointers_str (list): List of pointers defined by the initializer. Pointers store absolute labels.

    Generated Attributes:
        pointers (list): List of resolved pointers associated with the initializer (See resolve_pointers).

    The intended use of this class is to first parse the input attributes and then call the resolve_* functions
    """

    def __init__(self, path, start_line_number, name):
        self.path = path
        self.start_line_number = start_line_number
        self.name = name
        self.end_line_number = None
        self.pointers_str = []

        self.function_pointers = []
        self.constant_pointers = []
        self.unresolved_pointers = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def print(self):
        """Prints the details of the initializer."""
        print(f"Initializer: {self.name}")
        print(f"File: {self.path}")
        print(f"Start line: {self.start_line_number}")
        print(f"End line: {self.end_line_number}")
        print(f"Pointers: {self.pointers_str}")
        print(
            f"Resolved function pointers: {[fptr.name for fptr in self.function_pointers]}"
        )
        print(
            f"Resolved constant pointers: {[const.name for const in self.constant_pointers]}"
        )
        print(f"Unresolved pointers: {self.unresolved_pointers}")

    def resolve_pointers(self, functions, constants):
        for pointer_str in self.pointers_str:

            consts = constants_by_name(constants, pointer_str)
            if consts:
                glob = any(const.global_defs for const in consts)

                if glob:
                    if len(consts) > 1:
                        print(
                            f"Error: Conflicting definitions for global constant: {pointer_str}"
                        )
                        for const in consts:
                            print(f"In file {const.path}:{const.start_line_number}")
                        exit(1)
                    self.constant_pointers.append(consts[0])
                    debug.pdbg(
                        f"Initializer {self.name} in {self.path}:{self.start_line_number} defines pointer to global constant {pointer_str} in {consts[0].path}:{consts[0].start_line_number}"
                    )
                else:
                    for const in consts:
                        if const.path == self.path:
                            self.constant_pointers.append(const)
                            debug.pdbg(
                                f"Initializer {self.name} in {self.path}:{self.start_line_number} defines pointer to local constant {pointer_str} in {consts[0].path}:{consts[0].start_line_number}"
                            )
                continue

            funcs = functions_by_name(functions, pointer_str)
            if funcs:
                glob = any(func.global_defs for func in funcs)
                if glob:
                    if len(funcs) > 1:
                        print(
                            f"Error: Conflicting definitions for global function: {pointer_str}"
                        )
                        for func in funcs:
                            print(f"In file {func.path}:{func.start_line_number}")
                        exit(1)
                    self.function_pointers.append(funcs[0])
                    debug.pdbg(
                        f"Initializer {self.name} in {self.path}:{self.start_line_number} defines pointer to global function {pointer_str} in {funcs[0].path}:{funcs[0].start_line_number}"
                    )
                else:
                    for func in funcs:
                        if func.path == self.path:
                            self.function_pointers.append(func)
                            debug.pdbg(
                                f"Initializer {self.name} in {self.path}:{self.start_line_number} defines pointer to local function {pointer_str} in {funcs[0].path}:{funcs[0].start_line_number}"
                            )
                continue

            self.unresolved_pointers.append(pointer_str)
            debug.pdbg(
                f"Initializer {self.name} in {self.path}:{self.start_line_number} defines pointer to external symbol {pointer_str}"
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
                print(f"In file {function.path}:{function.start_line_number}")
                exit(1)
            ret = function
    return ret


def functions_referencing_external(functions, external_symbol):
    """
    Returns a list of function objects referencing an external symbol.

    Args:
        functions (list): List of Function objects.
        external_symbol (str): Name of the external symbol to match.

    Returns:
        list: List of matching Function objects.
    """
    return [
        function
        for function in functions
        if external_symbol in function.external_calls
        or external_symbol in function.external_constants
    ]


def initializers_referencing_external(initializers, external_symbol):
    """
    Returns a list of initializer objects referencing an external symbol.

    Args:
        initializers (list): List of Initializer objects.
        external_symbol (str): Name of the external symbol to match.

    Returns:
        list: List of matching Initializer objects.
    """
    return [
        initializer
        for initializer in initializers
        if external_symbol in initializer.unresolved_pointers
    ]


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
                print(f"In file {constant.path}:{constant.start_line_number}")
                exit(1)
            ret = constant
    return ret


def traverse_functions(functions, top):
    """
    Traverse all functions referenced by a function and return a list of all traversed functions.

    Args:
        functions (list): List of Function objects.
        top (Function): The top function to start traversal from.

    Returns:
        list: List of all traversed Function objects.
    """
    debug.pdbg(f"Traversing in {top.name} in {top.path}:{top.start_line_number}")

    ret = []

    for function in top.function_references:
        if function == top:
            continue

        ret += [function] + traverse_functions(functions, function)

    debug.pdbg(f"Traversing out {top.name} in {top.path}:{top.start_line_number}")

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


############################################
# Documentation
############################################

# Include private members in documentation
__pdoc__ = {
    name: True
    for name, _class in globals().items()
    if name.startswith("_") and isinstance(_class, type)
}
__pdoc__.update(
    {
        f"{name}.{member}": True
        for name, _class in globals().items()
        if isinstance(_class, type)
        for member in _class.__dict__.keys()
        if member not in {"__module__", "__dict__", "__weakref__", "__doc__"}
    }
)
