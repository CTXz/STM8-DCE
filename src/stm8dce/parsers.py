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
This module provides classes and functions to parse STM8 SDCC generated assembly files.
"""

from . import settings
from . import debug
from . import matchers
from . import analysis

############################################
# Classes
############################################


class FileIterator:
    """
    Class to iterate over lines in a file.

    Attributes:
        path (str): The path of the file.
        index (int): The current line number.
    """

    def __init__(self, f):
        """
        Initializes the FileIterator with the given file object.

        Args:
            f (file): The file object to iterate over.
        """
        self.path = f.name
        self.iterable = f.readlines()
        self.index = 0

    def __iter__(self):
        return self

    def next(self):
        """
        Returns the next line in the file.

        Returns:
            str: The next line in the file.

        Raises:
            StopIteration: If the end of the file is reached.
        """
        if self.index < len(self.iterable):
            ret = self.iterable[self.index]
            self.index += 1
            return ret
        else:
            raise StopIteration

    def prev(self):
        """
        Moves back one line in the file.

        Returns:
            str: The previous line in the file.

        Raises:
            StopIteration: If the beginning of the file is reached.
        """
        if self.index > 0:
            self.index -= 1
            return self.iterable[self.index]
        else:
            raise StopIteration


############################################
# Parsing
############################################


def parse_file(file):
    """
    Parses a file and returns a list of:
        - Function objects
        - GlobalDef objects
        - IntDef objects
        - Constant objects

    This function opens the file and creates a FileIterator.
    The actual parsing is done by the parse() function.

    Args:
        file (str): The path to the file to be parsed.

    Returns:
        tuple: A tuple containing lists of global definitions, interrupt definitions, constants, and functions.
    """
    if settings.debug:
        print()
        print(f"Parsing file: {file}")
        debug.pseperator()

    with open(file, "r") as f:
        fileit = FileIterator(f)
        return parse(fileit)


def parse(fileit):
    """
    Parses the file iterator and returns a list of:
        - Function objects
        - GlobalDef objects
        - IntDef objects
        - Constant objects

    Parsing includes:
        - Detecting global definitions
        - Detecting interrupt definitions
        - Detecting and parsing code sections (see parse_code_section)
        - Detecting and parsing constant sections (see parse_const_section)

    Args:
        fileit (FileIterator): The file iterator to parse.

    Returns:
        tuple: A tuple containing lists of global definitions, interrupt definitions, constants, and functions.
    """
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
                print(f"Line {fileit.index}: Global definition {global_defs}")

            continue

        # Interrupt definitions
        int_def = matchers.is_int_def(line)
        if int_def:
            interrupts.append(analysis.IntDef(fileit.path, int_def, fileit.index))

            if settings.debug:
                print(f"Line {fileit.index}: Interrupt definition {int_def}")

            continue

        # Code section
        area = matchers.is_area(line)
        if area == "CODE":
            functions += parse_code_section(fileit)

        # Constants section
        if area == "CONST":
            constants += parse_const_section(fileit)

    return globals, interrupts, constants, functions


def parse_code_section(fileit):
    """
    Parses the code section of the file and returns a list of Function objects within the code section.

    Parsing includes:
        - Detecting and parsing functions (see parse_function)
        - Detecting end of code section

    Args:
        fileit (FileIterator): The file iterator to parse.

    Returns:
        list: A list of Function objects.
    """
    if settings.debug:
        print(f"Line {fileit.index}: Code section starts here")

    functions = []
    while True:
        try:
            line = fileit.next()
        except StopIteration:
            break

        # Check if this is the end of the code section (start of a new area)
        area = matchers.is_area(line)
        if area:
            fileit.prev()  # Set back as this line is not part of the code section
            break

        # Parse function if a function label is found
        flabel = matchers.is_function_label(line)
        if flabel:
            functions += [parse_function(fileit, flabel)]

    if settings.debug:
        print(f"Line {fileit.index}: Code section ends here")

    return functions


def parse_const_section(fileit):
    """
    Parses the constants section of the file and returns a list of Constant objects.

    Parsing includes:
        - Detecting constants
        - Detecting end of constants section

    Args:
        fileit (FileIterator): The file iterator to parse.

    Returns:
        list: A list of Constant objects.
    """
    if settings.debug:
        print(f"Line {fileit.index}: Constants section starts here")

    constants = []
    while True:
        try:
            line = fileit.next()
        except StopIteration:
            break

        # Check if this is the end of the constants section (start of a new area)
        area = matchers.is_area(line)
        if area:
            fileit.prev()  # Set back as this line is not part of the constants section
            break

        # Parse constant if a constant label is found
        clabel = matchers.is_constant_label(line)
        if clabel:
            constants += [parse_constant(fileit, clabel)]

    if settings.debug:
        print(f"Line {fileit.index}: Constants section ends here")

    return constants


def parse_function(fileit, label):
    """
    Parses a function and returns a Function object.

    Parsing includes:
        - Detecting if the function is empty
        - Detecting calls made by the function
        - Detecting if the function is an IRQ handler
        - Detecting the end of the function

    Args:
        fileit (FileIterator): The file iterator to parse.
        label (str): The label of the function.

    Returns:
        Function: The parsed Function object.
    """
    if settings.debug:
        print(f"Line {fileit.index}: Function {label} starts here")

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
                print(f"Line {fileit.index}: Function {label} detected as IRQ Handler")
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
        if call:
            if settings.debug:
                print(f"Line {fileit.index}: Call to {call}")
            if call not in ret.calls_str:
                ret.calls_str.append(call)
            continue

        # Keep track of labels read by long address capable instructions
        # Note that calls are excluded from this list as they are already
        # handled above
        match = matchers.is_long_label_read(line)
        if match:
            op, lbls = match
            for l in lbls:
                if settings.debug:
                    print(
                        f"Line {fileit.index} ({op}): long address label {l} is read here"
                    )
                if l not in ret.long_read_labels_str:
                    ret.long_read_labels_str.append(l)
            continue

    if settings.debug:
        if ret.empty:
            print(f"Line {fileit.index}: Function {label} is empty!")
        print(f"Line {fileit.index}: Function {label} ends here")

    return ret


def parse_constant(fileit, label):
    """
    Parses a constant and returns a Constant object.

    Args:
        fileit (FileIterator): The file iterator to parse.
        label (str): The label of the constant.

    Returns:
        Constant: The parsed Constant object.
    """
    if settings.debug:
        print(f"Line {fileit.index}: Constant {label} starts here")

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
        print(f"Line {fileit.index}: Constant {label} ends here")

    return ret
