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
        print("Global:", self.name)
        print("File:", self.path)
        print("Line:", self.line)


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
        print("Interrupt:", self.name)
        print("File:", self.path)
        print("Line:", self.line)


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
        print("Function:", self.name)
        print("File:", self.path)
        print("Calls:", self.calls_str)
        print("Start line:", self.start_line)
        print("End line:", self.end_line)
        print("IRQ Handler:", self.isr_def)

    def resolve_globals(self, globals):
        """
        Resolves global definitions for the function.

        Args:
            globals (list): List of all GlobalDef objects.
        """
        for g in globals:
            if g.name == self.name:
                self.global_defs.append(g)
                if settings.debug:
                    print(
                        "Global in {}:{} matched to function {} in {}:{}".format(
                            g.path, g.line, self.name, self.path, self.start_line
                        )
                    )

    def resolve_isr(self, interrupts):
        """
        Resolves interrupt definitions for the function.

        Args:
            interrupts (list): List of all IntDef objects.
        """
        for i in interrupts:
            if i.name == self.name:
                self.isr_def = i
                if settings.debug:
                    print(
                        "Interrupt {}:{} matched to function {} in {}:{}".format(
                            i.path, i.line, self.name, self.path, self.start_line
                        )
                    )

    def resolve_calls(self, functions):
        """
        Resolves function calls for the function.

        Precondition: Globals of all functions have been resolved first.

        Args:
            functions (list): List of all Function objects.
        """
        for c in self.calls_str:
            funcs = functions_by_name(functions, c)

            glob = any(f.global_defs for f in funcs)

            if glob:
                if len(funcs) > 1:
                    print("Error: Conflicting definitions for non-static function:", c)
                    for f in funcs:
                        print("In file {}:{}".format(f.path, f.start_line))
                    exit(1)
                self.calls.append(funcs[0])
                if settings.debug:
                    print(
                        "Function {} in {}:{} calls function {} in {}:{}".format(
                            self.name,
                            self.path,
                            self.start_line,
                            funcs[0].name,
                            funcs[0].path,
                            funcs[0].start_line,
                        )
                    )
            else:
                matched = False
                for f in funcs:
                    if f.path == self.path:
                        if matched:
                            print(
                                "Error: Multiple static definitions for function {} in {}".format(
                                    f, f.path
                                )
                            )
                            exit(1)
                        self.calls.append(f)
                        if settings.debug:
                            print(
                                "Function {} in {}:{} calls static function {} in {}:{}".format(
                                    self.name,
                                    self.path,
                                    self.start_line,
                                    f.name,
                                    f.path,
                                    f.start_line,
                                )
                            )

    def resolve_fptrs(self, functions):
        """
        Resolves function pointers assigned by the function.

        Args:
            functions (list): List of all Function objects.
        """
        for l in self.long_read_labels_str:
            for f in functions:
                if f.name == l:
                    self.fptrs.append(f)
                    if settings.debug:
                        print(
                            "Function {} in {}:{} assigns function pointer to {} in {}:{}".format(
                                self.name,
                                self.path,
                                self.start_line,
                                f.name,
                                f.path,
                                f.start_line,
                            )
                        )

    def resolve_constants(self, constants):
        """
        Resolves constants for the function.

        Args:
            constants (list): List of all Constant objects.
        """
        for c in self.long_read_labels_str:
            consts = constants_by_name(constants, c)

            glob = any(c.global_defs for c in consts)

            if glob:
                if len(consts) > 1:
                    print("Error: Conflicting definitions for global constant:", c)
                    for c in consts:
                        print("In file {}:{}".format(c.path, c.start_line))
                    exit(1)
                self.constants.append(consts[0])
                if settings.debug:
                    print(
                        "Function {} in {}:{} reads global constant {} in {}:{}".format(
                            self.name,
                            self.path,
                            self.start_line,
                            c,
                            consts[0].path,
                            consts[0].start_line,
                        )
                    )
            else:
                for c in consts:
                    if c.path == self.path:
                        self.constants.append(c)
                        if settings.debug:
                            print(
                                "Function {} in {}:{} reads local constant {} in {}:{}".format(
                                    self.name,
                                    self.path,
                                    self.start_line,
                                    c,
                                    consts[0].path,
                                    consts[0].start_line,
                                )
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
        print("Constant:", self.name)
        print("File:", self.path)
        print("Start line:", self.start_line)
        print("End line:", self.end_line)

    def resolve_globals(self, globals):
        """
        Resolves global definitions for the constant.

        Args:
            globals (list): List of all GlobalDef objects.
        """
        for g in globals:
            if g.name == self.name:
                self.global_defs.append(g)
                if settings.debug:
                    print(
                        "Global in {}:{} matched to constant {} in {}:{}".format(
                            g.path, g.line, self.name, self.path, self.start_line
                        )
                    )


############################################
# Filtering & Search functions
############################################


def functions_by_name(functions, name):
    """
    Returns a list of function objects matching by name from a list of function objects.

    Args:
        functions (list): List of Function objects.
        name (str): Name of the function to match.

    Returns:
        list: List of matching Function objects.
    """
    return [f for f in functions if f.name == name]


def function_by_filename_name(functions, filename, name):
    """
    Returns a list of function objects matching by filename and name from a list of functions.

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
    for f in functions:
        f_filename = f.path.split("/")[-1]
        if f_filename == filename and f.name == name:
            if ret:
                print("Error: Multiple definitions for function:", name)
                print("In file {}:{}".format(f.path, f.start_line))
                exit(1)
            ret = f
    return ret


def constants_by_name(constants, name):
    """
    Returns a list of constant objects matching by name from a list of constants.

    Args:
        constants (list): List of Constant objects.
        name (str): Name of the constant to match.

    Returns:
        list: List of matching Constant objects.
    """
    return [c for c in constants if c.name == name]


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
    for c in constants:
        c_filename = c.path.split("/")[-1]
        if c_filename == filename and c.name == name:
            if ret:
                print("Error: Multiple definitions for constant:", name)
                print("In file {}:{}".format(c.path, c.start_line))
                exit(1)
            ret = c
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
        print("Traversing in {} in {}:{}".format(top.name, top.path, top.start_line))

    ret = []

    for call in top.calls:
        if call == top:
            continue

        ret += [call] + traverse_calls(functions, call)

    if settings.debug:
        print("Traversing out {} in {}:{}".format(top.name, top.path, top.start_line))

    return ret


def interrupt_handlers(functions):
    """
    Returns a list of all interrupt handlers in the list of functions.

    Args:
        functions (list): List of Function objects.

    Returns:
        list: List of interrupt handler Function objects.
    """
    return [f for f in functions if f.isr_def]
