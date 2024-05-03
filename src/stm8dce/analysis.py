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

# Description:
#   Classes and functions helpful for analyzing SDCC generated
#   STM8 assembly code

from . import settings

############################################
# Classes
############################################


# Class to store global definitions
# Includes:
#  - Path of the file the global is defined in
#  - Name of the global
#  - Line number of the global definition
class GlobalDef:
    def __init__(self, path, name, line):
        self.path = path
        self.name = name
        self.line = line

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def print(self):
        print("Global:", self.name)
        print("File:", self.path)
        print("Line:", self.line)


# Class to store interrupt definitions
# Equivalent to GlobalDef, but prints differently
class IntDef:
    def __init__(self, path, name, line):
        self.path = path
        self.name = name
        self.line = line

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def print(self):
        print("Interrupt:", self.name)
        print("File:", self.path)
        print("Line:", self.line)


# Class to store function definitions
# Includes:
#  - Path of the file the function is defined in
#  - Name of the function
#  - List of calls made by the function
#  - List of function pointers loaded by the function
#  - Start line of the function
#  - End line of the function
#  - Global definition/label assinged to the function
#  - If the function is an IRQ handler
#  - If the function is empty
class Function:
    def __init__(self, path, name, start_line):
        self.path = path
        self.name = name
        self.calls_str = []
        self.calls = []
        self.mem_loads_str = []
        self.constants = []
        self.start_line = start_line
        self.end_line = None
        self.global_defs = []
        self.fptrs = []
        self.isr_def = None
        self.empty = True

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def print(self):
        print("Function:", self.name)
        print("File:", self.path)
        print("Calls:", self.calls_str)
        print("Loads:", self.loads)
        print("Start line:", self.start_line)
        print("End line:", self.end_line)
        print("IRQ Handler:", self.isr)

    def resolve_globals(self, globals):
        # Get all matching global definitions
        for g in globals:
            if g.name == self.name:
                self.global_defs.append(g)
                if settings.debug:
                    print(
                        "Global in {}:{} matched to function {} in {}:{}".format(
                            g.path,
                            g.line,
                            self.name,
                            self.path,
                            self.start_line,
                        )
                    )

    def resolve_isr(self, interrupts):
        # Get all matching interrupt definitions
        for i in interrupts:
            if i.name == self.name:
                self.isr_def = i
                if settings.debug:
                    print(
                        "Interrupt {}:{} matched to function {} in {}:{}".format(
                            i.path, i.line, self.name, self.path, self.start_line
                        )
                    )

    # Precondition: Globals of all functions have been resolved first
    def resolve_calls(self, functions):
        # Get all matching functions called by this function
        for c in self.calls_str:
            funcs = functions_by_name(functions, c)

            # Check if either is defined globally/not-static
            glob = False
            for f in funcs:
                if f.global_defs:
                    glob = True
                    break

            # If function is defined globally, there can only be one instance!
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
            # Alternatively, there may be multiple static definitions
            # if so, choose the function within the same file
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
        for l in self.mem_loads_str:
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
        for c in self.mem_loads_str:
            consts = constants_by_name(constants, c)

            glob = False
            for c in consts:
                if c.global_defs:
                    glob = True
                    break

            if glob:
                if len(consts) > 1:
                    print("Error: Conflicting definitions for global constant:", c)
                    for c in consts:
                        print("In file {}:{}".format(c.path, c.start_line))
                    exit(1)
                self.constants.append(consts[0])
                if settings.debug:
                    print(
                        "Function {} in {}:{} loads global constant {} in {}:{}".format(
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
                                "Function {} in {}:{} loads local constant {} in {}:{}".format(
                                    self.name,
                                    self.path,
                                    self.start_line,
                                    c,
                                    consts[0].path,
                                    consts[0].start_line,
                                )
                            )


# Class to store constant definitions
class Constant:
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
        print("Constant:", self.name)
        print("File:", self.path)
        print("Start line:", self.start_line)
        print("End line:", self.end_line)

    def resolve_globals(self, globals):
        # Get all matching global definitions
        for g in globals:
            if g.name == self.name:
                self.global_defs.append(g)
                if settings.debug:
                    print(
                        "Global in {}:{} matched to constant {} in {}:{}".format(
                            g.path,
                            g.line,
                            self.name,
                            self.path,
                            self.start_line,
                        )
                    )


############################################
# Filtering & Search functions
############################################


# Returns the a list of function objects matching
# by name from a list of functions
def functions_by_name(functions, name):
    ret = []
    for f in functions:
        if f.name == name:
            ret.append(f)
    return ret


# Returns the a function object matching
# by filename and name from a list of functions
def function_by_filename_name(functions, filename, name):
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


# Returns the a list of constant objects matching
# by name from a list of constants
def constants_by_name(constants, name):
    ret = []
    for c in constants:
        if c.name == name:
            ret.append(c)
    return ret


# Returns the a list of constant objects matching
# by filename and name from a list of constants
def constant_by_filename_name(constants, filename, name):
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


# Traverse all calls made by a function and return a list of
# all functions
def traverse_calls(functions, top):
    if settings.debug:
        print("Traversing in {} in {}:{}".format(top.name, top.path, top.start_line))

    ret = []

    for call in top.calls:
        # Prevent infinite recursion
        if call == top:
            continue

        ret += [call] + traverse_calls(functions, call)

    if settings.debug:
        print("Traversing out {} in {}:{}".format(top.name, top.path, top.start_line))

    return ret


# Returns a list of all interrupt handlers in the list of functions
def interrupt_handlers(functions):
    ret = []
    for f in functions:
        if f.isr_def:
            ret.append(f)
    return ret
