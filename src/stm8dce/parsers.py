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
#   Classes and Functions to parse STM8 SDCC generated assembly files

from . import settings
from . import debug
from . import matchers
from . import analysis

############################################
# Classes
############################################


# Class to iterate over lines in a file
# Notably it include:
#   - A prev() function to move back one line
#   - A path attribute to store the path of the file
#   - An index attribute to store the current line number
class FileIterator:
    def __init__(self, f):
        self.path = f.name
        self.iterable = f.readlines()
        self.index = 0

    def __iter__(self):
        return self

    def next(self):
        if self.index < len(self.iterable):
            ret = self.iterable[self.index]
            self.index += 1
            return ret
        else:
            raise StopIteration

    def prev(self):
        if self.index > 0:
            self.index -= 1
            return self.iterable[self.index]
        else:
            raise StopIteration


############################################
# Parsing
############################################


# Parses a file and returns a list of:
#   - Function objects
#   - GlobalDef objects
#   - IntDef objects
#   - Constant objects
# This function opens the file and creates a FileIterator
# The actual parsing is done by the parse() function
def parse_file(file):
    if settings.debug:
        print()
        print("Parsing file:", file)
        debug.pseperator()

    with open(file, "r") as f:
        fileit = FileIterator(f)
        return parse(fileit)


# Parses the file iterator and returns a list of:
#   - Function objects
#   - GlobalDef objects
#   - IntDef objects
#   - Constant objects
# Parsing includes:
#   - Detecting global definitions
#   - Detecting and parsing code sections
def parse(fileit):
    globals = []
    interrupts = []
    functions = []
    constants = []
    while True:
        try:
            line = fileit.next()
        except StopIteration:
            break

        # Global definitions
        global_defs = matchers.is_global_defs(line)
        if global_defs:
            globals.append(analysis.GlobalDef(fileit.path, global_defs, fileit.index))

            if settings.debug:
                print("Line {}: Global definition {}".format(fileit.index, global_defs))

            continue

        # Interrupt definitions
        int_def = matchers.is_int_def(line)
        if int_def:
            interrupts.append(analysis.IntDef(fileit.path, int_def, fileit.index))

            if settings.debug:
                print("Line {}: Interrupt definition {}".format(fileit.index, int_def))

            continue

        # Code section
        area = matchers.is_area(line)
        if area == "CODE":
            functions += parse_code_section(fileit)

        # Constants section
        if area == "CONST":
            constants += parse_const_section(fileit)

    return globals, interrupts, constants, functions


# Parses the code section of the file
# Returns a list of Function objects within the code section
# Parsing includes:
#  - Detecting and parsing functions
#  - Detecting end of code section
def parse_code_section(fileit):
    if settings.debug:
        print("Line {}: Code section starts here".format(fileit.index))

    functions = []
    while True:
        try:
            line = fileit.next()
        except StopIteration:
            break

        area = matchers.is_area(line)
        if area:
            fileit.prev()  # Set back as this line is not part of the code section
            break

        flabel = matchers.is_function_label(line)
        if flabel:
            functions += [parse_function(fileit, flabel)]

    if settings.debug:
        print("Line {}: Code section ends here".format(fileit.index))

    return functions


def parse_const_section(fileit):
    if settings.debug:
        print("Line {}: Constants section starts here".format(fileit.index))

    constants = []
    while True:
        try:
            line = fileit.next()
        except StopIteration:
            break

        area = matchers.is_area(line)
        if area:
            fileit.prev()  # Set back as this line is not part of the constants section
            break

        clabel = matchers.is_constant_label(line)
        if clabel:
            constants += [parse_constant(fileit, clabel)]

    if settings.debug:
        print("Line {}: Constants section ends here".format(fileit.index))

    return constants


# Parses a function and returns a Function object
# Parsing includes:
#  - Detecting calls made by the function
#  - Detecting if the function is empty
#  - Detecting if the function is an IRQ handler
#  - Detecting the end of the function
def parse_function(fileit, label):
    if settings.debug:
        print("Line {}: Function {} starts here".format(fileit.index, label))

    ret = analysis.Function(fileit.path, label, fileit.index)
    while True:
        try:
            line = fileit.next()
        except StopIteration:
            break

        # Ignore comments
        if matchers.is_comment(line):
            continue

        # Check if this is an IRQ handler
        if matchers.is_iret(line):
            if settings.debug:
                print(
                    "Line {}: Function {} detected as IRQ Handler".format(
                        fileit.index, label
                    )
                )
            ret.isr = True
            continue

        # Check if this is the end of the function
        if matchers.is_function_label(line) or matchers.is_area(line):
            # Set back as this line is not part of the function
            fileit.prev()
            ret.end_line = fileit.index
            break

        # From here on we can assume the function is not empty
        ret.empty = False

        # Keep track of calls made by this function
        call = matchers.is_call(line)
        if call and (call not in ret.calls_str):
            if settings.debug:
                print("Line {}: Call to {}".format(fileit.index, call))
            ret.calls_str.append(call)
            continue

        # Keep track of loads with labels as src (these are likely constants)
        load = matchers.is_load_src_label(line)
        if load and (load not in ret.mem_loads_str):
            if settings.debug:
                print("Line {}: Load with label as src {}".format(fileit.index, load))
            ret.mem_loads_str.append(load)
            continue

    if settings.debug:
        if ret.empty:
            print("Line {}: Function {} is empty!".format(fileit.index, label))
        print("Line {}: Function {} ends here".format(fileit.index, label))

    return ret


def parse_constant(fileit, label):
    if settings.debug:
        print("Line {}: Constant {} starts here".format(fileit.index, label))

    ret = analysis.Constant(fileit.path, label, fileit.index)
    while True:
        try:
            line = fileit.next()
        except StopIteration:
            break

        # Ignore comments
        if matchers.is_comment(line):
            continue

        # Check if this is the end of the constant
        if matchers.is_constant_label(line) or matchers.is_area(line):
            # Set back as this line is not part of the constant
            fileit.prev()
            ret.end_line = fileit.index
            break

    if settings.debug:
        print("Line {}: Constant {} ends here".format(fileit.index, label))

    return ret
